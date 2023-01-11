`timescale 1ns/1ps

module #(1) a(input x, input y, output z); assign z = x & y; endmodule module b(input x, input y, output z); assign z = x | y; endmodule   module c(input x, input y, output z); assign z = x ^ y; endmodule

module multiline ( input a,
input b,
input c);

endmodule

module soc2tc #(parameter WIDTH = 7)
(
  // signed original code: soc[WIDTH-1] indicates sign. Res are abosolute value;
  input  [WIDTH-1:0]      soc, 
  // 2's complement
  output wire [WIDTH-1:0] tc  
);
/*convert N-bit signed orignal code to N-bit two's complement code*/
wire [WIDTH-2:0] bra1 = ~soc[WIDTH-2:0] + 1'b1; //bit by bit reverse then add 1; 
assign tc = ~soc[WIDTH-1] ? soc
          : soc[WIDTH-2:0] == 0 ? 0 : {1'b1, bra1};
endmodule module tc2soc #(parameter WIDTH = 7)
(
  // 2's complement
  input       [WIDTH-1:0] tc,
  // signed original code: soc[WIDTH-1] indicates sign. Res are abosolute value;
  output wire [WIDTH-1:0] soc,
  // overflow is 1 when tc == 0b1000..00
  output wire             overflow
);
/*convert N-bit two's complement code to N-bit signed orignal code*/
assign overflow = tc[WIDTH-1] && ~(|tc[WIDTH-2:0]);
wire [WIDTH-2:0] bra1 = ~tc[WIDTH-2:0] + 1'b1; //bit by bit reverse then add 1; 
assign soc = tc[WIDTH-1] ? {1'b1, bra1} : tc;
endmodule

module cmp_clbrt(
    input             clk,
    input             rstn,
    input             en,
    input             cpr_out,
    input       [6:0] offset,
    input             base_wen,
    input       [3:0] base_wdata,
    output wire       done,
    output wire       timeout,
    output wire [6:0] reff,
    output reg        base_overflow,     
    output wire       overflow  // when overflow == 1, the reff stays at max/min value
);

/* Data Format Convert */
// tc stands for two-complement code
// sum_tc = offset_tc + base_tc when enable offset
// sum_tc = base_tc when not enable offset
wire       enable_offset;
wire [6:0] sum;
wire [6:0] sum_tc;
wire [6:0] offset_tc;
wire [3:0] base_wdata_tc;
reg  [3:0] base_tc;
wire [6:0] base_tc_extend = { {3{base_tc[3]}}, base_tc}; // signed extendency
assign sum_tc = enable_offset ?
                $signed(offset_tc) + $signed(base_tc_extend) : $signed(base_tc_extend);

soc2tc #(.WIDTH(4)) base_wdata_soc2tc
(
  .soc(base_wdata),
  .tc(base_wdata_tc)
);

soc2tc #(.WIDTH(7)) offset_soc2tc
(
  .soc(offset),
  .tc(offset_tc)
);

wire convert_overflow;
tc2soc #(.WIDTH(7)) reff_tc2soc
(
  .tc(sum_tc),
  .soc(sum),
  .overflow(convert_overflow)
);

// overflow judge
/// base + offset out of range
wire upflow   = ~offset_tc[6] && ~base_tc_extend[6] && sum_tc[6];
wire downflow = offset_tc[6] && base_tc_extend[6] && ~sum_tc[6]
                 || convert_overflow;
assign overflow = upflow || downflow;

/// overflow condition (statisfy any of below):
///   a. sum_tc is 0b100...000 (tc range is large than soc since no negative 0)
///   b. offset and base are both positive, but the sum reff is negative
///   c. offset and base are both negative, but the sum reff is positive
assign reff = upflow   ? 7'b0111111 : // when upper bound overflow, take max value
              downflow ? 7'b1111111 : // when lower bound overflow, take min value
              sum;                    // when no overflow, take the summation



/* Main State Machine Variables */
localparam IDLE = 4'b0001; //not even start
localparam CLBR = 4'b0010; //doing calibration
localparam DONE = 4'b0100; //calibration done
localparam TOUT = 4'b1000; //timeout
reg [3:0] state, next_state;

/* Adjust Variables */
localparam ADJ_DEC = 1'b0;
localparam ADJ_INC = 1'b1;
reg [4:0]  adj_mnt; // adjust record: 1 stands for maintaining
reg [4:0]  adj_rcd; // adjust record; when adj_mnt[i] == 0, adj_rcd[i] is 1 for increasing and 0 for decreasing
reg [4:0]  adj_cnt; // adjust times counter; at most 32 times.
wire done_pattern_match_0 = state == CLBR && adj_mnt == 5'b11111;
wire done_pattern_match_1 = state == CLBR && adj_mnt == 5'b00000 && 
                            (adj_rcd == 5'b10101 || adj_rcd == 5'b01010);
wire done_pattern_match = done_pattern_match_0 || done_pattern_match_1;



/* Main State Machine */
always @(posedge clk or negedge rstn) begin
    if(~rstn)
        state <= IDLE;
    else
        state <= next_state;  
end

assign done    = state == DONE;
assign timeout = state == TOUT;
assign enable_offset = state == IDLE || done || timeout;

always@(*) begin
    case(state)
        IDLE: next_state = en ? CLBR : IDLE;
        CLBR: next_state = adj_cnt == 5'b11111 ? TOUT
                         : done_pattern_match  ? DONE : CLBR;
        DONE: next_state = DONE;//note
        TOUT: next_state = TOUT;//note
        default: next_state = IDLE;
    endcase
end

/* Calibration */
/// The calibration process contains up to 32 adjustment;
/// For each adjustment, cpr_out will be sampled 500 times;
/// The times that cpr_out is 1 will be recorded in reg one_cnt:
///   if one_cnt belongs to [275, +inf), increase base_tc
///   if one_cnt belongs to [0,   225 ], decrease bese_tc
///   if one_cnt belongs to [225, 275 ], maintain
///   (Suppose that reff exactly equals to comparators + input, then the probability
///    that cpr_out is 1 should equals to 1/2; the probability that one_cnt are in 
///    interval [225, 275] is about 0.972                                           )
/// After each adjustment: 
///   if the pattern for done is matched, calibration is done;
///   if calibration 32 times, done pattern is not matched, then time out.

reg [8:0] smpl_cnt;    //In each calibration, the times that sample cpr_out 
reg [8:0] one_cnt;     //In each calibration, the times that cpr_out is 1
wire lt = one_cnt > 9'b1_0001_0011; // one_cnt > 275
wire st = one_cnt < 9'b0_1110_0001; // one_cnt < 225

// sample
always@(posedge clk or negedge rstn) begin
    if(~rstn) 
        smpl_cnt <= 9'b0;
    else if(state == CLBR)
    /// smpl_cnt goes through 0-500, however, only when smpl_cnt belongs to
    /// {0, 1, ... 499}, the cpr_out will be sampled (only sample 500 times)
    /// when smpl_cnt is 500, the adjustment is taken
        smpl_cnt <= smpl_cnt == 9'b1_1111_0100 ? 9'b0 : smpl_cnt + 1'b1;
    else
        smpl_cnt <= 9'b0;            
end

always@(posedge clk or negedge rstn) begin
    if(~rstn)
        one_cnt <= 9'b0;
    else if(state == CLBR) begin
        if(smpl_cnt == 9'b1_1111_0100)
            /// when smpl_cnt == 500, do not sample but adjust
            one_cnt <= 9'b0;
        else
            one_cnt <= cpr_out ? one_cnt + 1'b1 : one_cnt;
    end
    else
        one_cnt <= 9'b0;
end

// adjust base
reg [3:0] fsm_base_tc; // base_tc value inside fsm
reg [3:0] state_d;

always@(posedge clk or negedge rstn) begin
    if(~rstn)
        state_d <= IDLE;
    else
        state_d <= state;
end

always@(posedge clk or negedge rstn) begin
    if(~rstn)
        base_tc       <= 4'b0;
    else begin
        if(base_wen)
            base_tc <= base_wdata_tc;
        else if(state_d == CLBR)
            base_tc <= fsm_base_tc;
    end  
end

always @(posedge clk or negedge rstn) begin
    if(~rstn) begin
        fsm_base_tc   <= 4'b0;
        adj_cnt       <= 5'b0;
        adj_mnt       <= 5'b0;
        adj_rcd       <= 5'b0;
    end
    else begin
        if(state == IDLE) begin
            fsm_base_tc   <= 4'b0;
            adj_cnt       <= 5'b0;
            adj_mnt       <= 5'b0;
            adj_rcd       <= 5'b0;
        end
        else if(state == CLBR) begin
            if(smpl_cnt == 9'b1_1111_0100) begin
            /// when smpl_cnt == 500, adjust
                adj_cnt <= adj_cnt + 1'b1;
                if(lt) begin
                    if(fsm_base_tc != 4'b0111)
                        fsm_base_tc <= $signed(fsm_base_tc) + $signed(4'b1);
                    adj_mnt <= {adj_mnt[3:0], 1'b0};
                    adj_rcd <= {adj_rcd[3:0], ADJ_INC};
                end
                else if(st) begin //if(st)
                    if(fsm_base_tc != 4'b1001)
                        fsm_base_tc <= $signed(fsm_base_tc) - $signed(4'b1);
                    adj_mnt <= {adj_mnt[3:0], 1'b0};
                    adj_rcd <= {adj_rcd[3:0], ADJ_DEC};
                end
                else begin
                    adj_mnt <= {adj_mnt[3:0], 1'b1};
                    adj_rcd <= {adj_rcd[3:0], 1'b0};
                end
            end
        end       
    end
end

endmodule
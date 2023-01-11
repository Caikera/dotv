module soc2tc #(parameter WIDTH = 7)
(
  input  [WIDTH-1:0]      soc, 
  output wire [WIDTH-1:0] tc  
);
wire [WIDTH-2:0] bra1 = ~soc[WIDTH-2:0] + 1'b1; 
assign tc = ~soc[WIDTH-1] ? soc
          : soc[WIDTH-2:0] == 0 ? 0 : {1'b1, bra1};
endmodule
module tc2soc #(parameter WIDTH = 7)
(
  input       [WIDTH-1:0] tc,
  output wire [WIDTH-1:0] soc,
  output wire             overflow
);
assign overflow = tc[WIDTH-1] && ~(|tc[WIDTH-2:0]);
wire [WIDTH-2:0] bra1 = ~tc[WIDTH-2:0] + 1'b1; 
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
    output wire       overflow  
);
wire       enable_offset;
wire [6:0] sum;
wire [6:0] sum_tc;
wire [6:0] offset_tc;
wire [3:0] base_wdata_tc;
reg  [3:0] base_tc;
wire [6:0] base_tc_extend = { {3{base_tc[3]}}, base_tc}; 
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
wire upflow   = ~offset_tc[6] && ~base_tc_extend[6] && sum_tc[6];
wire downflow = offset_tc[6] && base_tc_extend[6] && ~sum_tc[6]
                 || convert_overflow;
assign overflow = upflow || downflow;
assign reff = upflow   ? 7'b0111111 : 
              downflow ? 7'b1111111 : 
              sum;                    
localparam IDLE = 4'b0001; 
localparam CLBR = 4'b0010; 
localparam DONE = 4'b0100; 
localparam TOUT = 4'b1000; 
reg [3:0] state, next_state;
localparam ADJ_DEC = 1'b0;
localparam ADJ_INC = 1'b1;
reg [4:0]  adj_mnt; 
reg [4:0]  adj_rcd; 
reg [4:0]  adj_cnt; 
wire done_pattern_match_0 = state == CLBR && adj_mnt == 5'b11111;
wire done_pattern_match_1 = state == CLBR && adj_mnt == 5'b00000 && 
                            (adj_rcd == 5'b10101 || adj_rcd == 5'b01010);
wire done_pattern_match = done_pattern_match_0 || done_pattern_match_1;
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
        DONE: next_state = DONE;
        TOUT: next_state = TOUT;
        default: next_state = IDLE;
    endcase
end
reg [8:0] smpl_cnt;    
reg [8:0] one_cnt;     
wire lt = one_cnt > 9'b1_0001_0011; 
wire st = one_cnt < 9'b0_1110_0001; 
always@(posedge clk or negedge rstn) begin
    if(~rstn) 
        smpl_cnt <= 9'b0;
    else if(state == CLBR)
        smpl_cnt <= smpl_cnt == 9'b1_1111_0100 ? 9'b0 : smpl_cnt + 1'b1;
    else
        smpl_cnt <= 9'b0;            
end
always@(posedge clk or negedge rstn) begin
    if(~rstn)
        one_cnt <= 9'b0;
    else if(state == CLBR) begin
        if(smpl_cnt == 9'b1_1111_0100)
            one_cnt <= 9'b0;
        else
            one_cnt <= cpr_out ? one_cnt + 1'b1 : one_cnt;
    end
    else
        one_cnt <= 9'b0;
end
reg [3:0] fsm_base_tc; 
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
                adj_cnt <= adj_cnt + 1'b1;
                if(lt) begin
                    if(fsm_base_tc != 4'b0111)
                        fsm_base_tc <= $signed(fsm_base_tc) + $signed(4'b1);
                    adj_mnt <= {adj_mnt[3:0], 1'b0};
                    adj_rcd <= {adj_rcd[3:0], ADJ_INC};
                end
                else if(st) begin 
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
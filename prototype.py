import dataclasses
import yaml
import json

import log
from lexer import literal_pat_0, literal_pat_1, literal_pat_2
from parser import Parser, ParserError, SourceInfo
from syntax.node import DataTypeNode, ModuleNode, AnsiPortDefNode, NonAnsiPortDefNode, PortDefAndInitInBodyNode, ParamDefInBodyNode
from syntax.expression import Expression, Identifier, Literal

log = log.log


@dataclasses.dataclass
class ParameterInfo:
    name: str
    data_type: str | None
    default_val: str
    pos: (int, int)


@dataclasses.dataclass
class PortInfo:
    name: str
    direction: str  # input / output / inout
    data_type: str | None
    width: str | None
    pos_ansi: (int, int)
    pos_non_ansi_0: (int, int)
    pos_non_ansi_1: (int, int)


@dataclasses.dataclass
class ModulePrototypeInfo:
    name: str
    parameters: list[ParameterInfo]
    port: list[PortInfo]
    pos: (int, int)


def extract_module_prototype_info_from_file_to_yml(i: str, o: str, enable_non_ansi: bool = True):
    info_s = extract_module_prototype_info_from_file(i, enable_non_ansi)
    info_dict_s = [dataclasses.asdict(info) for info in info_s]
    with open(o, 'w', encoding="utf-8") as f:
        json.dump(info_dict_s, f, indent=4)
        log.hint(f"module prototype info has been written to '{o}'\n")


def extract_module_prototype_info_from_file(path: str, enable_non_ansi: bool = True) -> list[ModulePrototypeInfo]:
    with open(path, 'r', encoding="utf-8") as f:
        verilog = f.read()
    parser = Parser(verilog, parse_body=enable_non_ansi)
    nodes = parser.parse()
    src_info = parser.ctx.src_info

    info_s = []
    for node in nodes:
        if isinstance(node, ModuleNode):
            log.info(f"extracting prototype info from module {node.name} ... \n")
            info_s.append(extract_module_prototype_info_from_node(node,
                                                                  src_info=src_info,
                                                                  enable_non_ansi=enable_non_ansi))
    return info_s


def extract_module_prototype_info_from_node(node: ModuleNode,
                                            src_info: SourceInfo,
                                            enable_non_ansi: bool = True) -> ModulePrototypeInfo | None:
    name = node.name

    """ parameter """
    parameter_s = {}
    if node.paras is not None:
        for para in node.paras:
            if para.data_type is None:
                para_data_type = None
            else:
                para_data_type = para.data_type.tokens_str
            for identifier_array, val in para.identifier_array_val_pairs:
                para_name = identifier_array.identifier.src
                if para_name in parameter_s.keys():
                    log.fatal(f"duplicated parameter name '{para_name}' in module '{node.name}'\n")
                    raise ParserError
                parameter_s[para_name] = {'data_type': para_data_type, 'default_val': val.tokens_str,
                                          'pos': identifier_array.identifier.pos}
        for item in node.body_items:
            if not isinstance(item, ParamDefInBodyNode):
                continue
            if item.data_type is None:
                para_data_type = None
            else:
                para_data_type = item.data_type.tokens_str
            for identifier_array, val in item.identifier_array_val_pairs:
                para_name = identifier_array.identifier.src
                if para_name in parameter_s.keys():
                    log.fatal(f"duplicated parameter name '{para_name}' in module '{node.name}'\n")
                    raise ParserError
                parameter_s[para_name] = {'data_type': para_data_type, 'default_val': val.tokens_str,
                                          'pos': identifier_array.identifier.pos}

    parameter_info_s = []
    for parameter in parameter_s:
        parameter_info = ParameterInfo(name=parameter, data_type=parameter_s[parameter]['data_type'],
                                       default_val=parameter_s[parameter]['default_val'],
                                       pos=parameter_s[parameter]['pos'])
        parameter_info_s.append(parameter_info)

    """ port """
    port_s = {}
    if node.ports is not None and len(node.ports) != 0:
        if isinstance(node.ports[0], AnsiPortDefNode):
            # ANSI
            for port in node.ports:
                assert isinstance(port, AnsiPortDefNode)
                port_direction = port.direction.src
                if port.data_type is None:
                    port_data_type = None
                    port_width = None
                else:
                    port_data_type = port.data_type.tokens_str
                    port_width, vars = get_width_from_data_type(port.data_type)
                    for var in vars:
                        if var not in parameter_s.keys():
                            log.fatal(f"variable '{var}' is not defined as parameter in module '{node.name}', but it "
                                      f"is used in port's range '{port.data_type.tokens_str}'\n")
                            raise ParserError
                for identifier_array in port.array_identifiers:
                    port_name = identifier_array.identifier.src
                    if port_name in port_s.keys():
                        log.fatal(f"duplicated port name '{port_name}' in module '{node.name}'\n")
                        raise ParserError
                    port_s[port_name] = {'direction': port_direction,
                                         'data_type': port_data_type,
                                         'width': port_width,
                                         'pos_ansi': identifier_array.identifier.pos,
                                         'pos_non_ansi_0': None,
                                         'pos_non_ansi_1': None}
        else:
            # Non-Ansi
            if not enable_non_ansi:
                log.fatal(f"enable_non_ansi is set to False, but module '{node.name}' has Non-ANSI ports definition.\n")
                raise ParserError
            port_s = {}
            for port in node.ports:
                assert isinstance(port, NonAnsiPortDefNode)
                port_name = port.identifier.src
                if port_name in port_s.keys():
                    log.fatal(f"duplicated port name '{port_name}' in module '{node.name}'\n")
                    raise ParserError
                port_s[port_name] = {'direction': None,
                                     'data_type': None,
                                     'width': None,
                                     'pos_ansi': None,
                                     'pos_non_ansi_0': port.tokens[0].pos,
                                     'pos_non_ansi_1': None}
            for item in node.body_items:
                if not isinstance(item, PortDefAndInitInBodyNode):
                    continue
                assert isinstance(item, PortDefAndInitInBodyNode)
                port_direction = item.direction.src
                if item.data_type is None:
                    port_data_type = None
                    width = None
                else:
                    port_data_type = item.data_type.tokens_str
                    width, vars = get_width_from_data_type(item.data_type)
                    for var in vars:
                        if var not in parameter_s.keys():
                            log.fatal(f"variable '{var}' is not defined as parameter in module '{node.name}', but it "
                                      f"is used in port's range '{item.data_type.tokens_str}'\n")
                            raise ParserError
                for identifier_array, val in item.identifier_array_val_pairs:
                    port_name = identifier_array.identifier.src
                    if port_name not in port_s.keys():
                        log.fatal(f"in-consistent port definition between Non-ANSI list and module body details, "
                                  f"'{port_name}' is not defined in the Non-ANSI list for module '{node.name}'.\n")
                        raise ParserError
                    if port_s[port_name]["direction"] is not None:
                        log.fatal(f"duplicated port definition detail '{port_name}' in module '{node.name}'\n")
                        raise ParserError
                    port_s[port_name]["direction"] = port_direction
                    port_s[port_name]["data_type"] = port_data_type
                    port_s[port_name]["width"] = width
                    port_s[port_name]["pos_non_ansi_1"] = identifier_array.identifier.pos

    port_info_s = []
    for port_name, port_property in port_s.items():
        if port_property["direction"] is None:
            log.fatal(f"in-complete port definition, the direction is not specified, '{port_name}' in module '{node.name}'\n")
        port_info = PortInfo(name=port_name,
                             direction=port_property["direction"],
                             data_type=port_property["data_type"],
                             width=port_property["width"],
                             pos_ansi=port_property["pos_ansi"],
                             pos_non_ansi_0=port_property["pos_non_ansi_0"],
                             pos_non_ansi_1=port_property["pos_non_ansi_1"])
        port_info_s.append(port_info)

    return ModulePrototypeInfo(name=name, parameters=parameter_info_s, port=port_info_s,
                               pos=node.tokens[0].pos)


def get_width_from_data_type(data_type: DataTypeNode) -> (str | None, set[str]):
    range_ = data_type.range_
    if range_ is None:
        return None, []
    else:
        # right
        right = range_.right.tokens_str
        right_val = -1
        if not isinstance(range_.right, Literal):
            log.fatal(f"unsupported width defined by range '{range_.tokens_str}', the lower-index should be 0.\n")
            raise ParserError
        if literal_pat_2.match(right):
            cap = literal_pat_2.match(right)
            right_val = int(cap.group(0))
        elif literal_pat_1.match(right):
            log.fatal(f"the range index should be an integer: '{range_.tokens_str}'\n")
            raise ParserError
        elif literal_pat_0.match(right):
            cap = literal_pat_0.match(right)
            width = cap.group(1)
            signed = cap.group(2)
            base = cap.group(3)
            if base in ['h', 'H']:
                base = 16
            elif base in ['d', 'D']:
                base = 10
            elif base in ['o', 'O']:
                base = 8
            else:
                base = 2
            right_val = int(cap.group(4), base=base)

        if right_val != 0:
            log.fatal(f"unsupported width defined by range '{range_.tokens_str}', the lower-index should be 0.\n")
            raise ParserError

        # left
        left = range_.left.tokens_str
        if isinstance(range_.left, Literal):
            left_val = -1
            if literal_pat_2.match(left):
                cap = literal_pat_2.match(left)
                left_val = int(cap.group(0))
            elif literal_pat_1.match(left):
                log.fatal(f"the range index should be an integer: '{range_.tokens_str}'\n")
                raise ParserError
            elif literal_pat_0.match(left):
                cap = literal_pat_0.match(left)
                width = cap.group(1)
                signed = cap.group(2)
                base = cap.group(3)
                if base in ['h', 'H']:
                    base = 16
                elif base in ['d', 'D']:
                    base = 10
                elif base in ['o', 'O']:
                    base = 8
                else:
                    base = 2
                left_val = int(cap.group(4), base=base)
            vars = set()
            extract_identifier_names_from_expr(range_.left, vars)
            return f"{left_val+1}", vars
        else:
            vars = set()
            extract_identifier_names_from_expr(range_.left, vars)
            return f"{left} + 1", vars


def extract_identifier_names_from_expr(expr: Expression, identifier_name_s: set[str]):
    if isinstance(expr, Identifier):
        identifier_name_s.add(expr.identifier.src)
        return
    else:
        for k, v in expr.__dict__.items():
            if isinstance(v, list):
                for vc in v:
                    if isinstance(v, Expression):
                        extract_identifier_names_from_expr(vc, identifier_name_s)
            elif isinstance(v, Expression):
                extract_identifier_names_from_expr(v, identifier_name_s)
        return


if __name__ == "__main__":
    extract_module_prototype_info_from_file_to_yml("./rich_grammar.sv", "./prototype.yml", enable_non_ansi=True)
    _ = extract_module_prototype_info_from_file("./rich_grammar.sv", enable_non_ansi=True)

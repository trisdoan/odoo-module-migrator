# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import re
from odoo_module_migrate.base_migration_script import BaseMigrationScript
from pathlib import Path
import sys
import os
import ast
from typing import Any
from astroid import ClassDef, FunctionDef, NodeNG, nodes

# TODO: list all cases to handle
## 1st: _("Cash difference observed during the counting (%s)") % name -> _("Cash difference observed during the counting (%s)", name)
## 2nd: use .format -> _("It's %s", 2024)


### TODO: list all test cases


class VisitorPlaceHolder(ast.NodeVisitor):
    def visit_Call(self, node):
        # Check if the function is a translation function
        if isinstance(node.func, ast.Name) and node.func.id == "(":
            if node.args:
                arg = node.args[0]
                print(f"Visiting node: {ast.dump(node)}")
                # Case 1: Using % formatting
                if isinstance(arg, ast.BinOp) and arg.op == "%":
                    print("case 1")
                    # if isinstance(arg.left, ast.Str):
                    #     # Convert to new syntax
                    #     new_args = [arg.left] + [arg.right]
                    #     return ast.Call(func=node.func, args=new_args, keywords=[])
                # Case 2: Using .format()
                elif (
                    isinstance(arg, ast.Call)
                    and isinstance(arg.func, ast.Attribute)
                    and arg.func.attr == "format"
                ):
                    print("case 2")
                    # if isinstance(arg.func.value, ast.Str):
                    #     # Convert to new syntax
                    #     new_args = [arg.func.value] + arg.args
                    #     return ast.Call(func=node.func, args=new_args, keywords=[])
        return self.generic_visit(node)

    # def post_process(self, all_code: str, file: str) -> str:
    #     all_lines = all_code.split("\n")
    #     for i, line in enumerate(all_lines):
    #         if "_(" in line:
    #             print("testing", line)
    #     return "\n".join(all_lines)


def _replace_translation_syntax(logger, filename):
    with open(filename, mode="rt") as file:
        new_all = all_code = file.read()
        # only reduce logger for impact file
        visitor = VisitorPlaceHolder()
        try:
            tree = ast.parse(new_all)
            tree = visitor.visit(tree)
        except Exception:
            logger.info(f"ERROR in {filename} at step {visitor.__class__}: \n{new_all}")
            raise
        # new_all = visitor.post_process(new_all, filename)
        # if new_all == all_code:
        #     logger.info("read_group detected but not changed in file %s" % filename)

    if new_all != all_code:
        logger.info("Script read_group replace applied in file %s" % filename)
        with open(filename, mode="wt") as file:
            file.write(new_all)


def _get_files(module_path, reformat_file_ext):
    """Get files to be reformatted."""
    file_paths = list()
    if not module_path.is_dir():
        raise Exception(f"'{module_path}' is not a directory")
    file_paths.extend(module_path.rglob("*" + reformat_file_ext))
    return file_paths


def replace_translation_syntax(
    logger, module_path, module_name, manifest_path, migration_steps, tools
):
    reformat_file_ext = ".py"
    file_paths = _get_files(module_path, reformat_file_ext)
    logger.debug(f"{reformat_file_ext} files found:\n" f"{list(map(str, file_paths))}")

    reformatted_files = list()
    for file_path in file_paths:
        reformatted_file = _replace_translation_syntax(logger, file_path)
        if reformatted_file:
            reformatted_files.append(reformatted_file)
    logger.debug("Reformatted files:\n" f"{list(reformatted_files)}")


class MigrationScript(BaseMigrationScript):

    _GLOBAL_FUNCTIONS = [replace_translation_syntax]

#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Replace useless unpacking with multiple assignments where possible."""

from .OptimizeBase import OptimizationVisitorBase, makeRaiseExceptionReplacementStatement

from nuitka.nodes import Nodes

class ReplaceUnpackingVisitor( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isStatementAssignment():
            targets = node.getTargets()

            if len( targets ) == 1:
                target = targets[0]

                if target.isAssignTargetTuple():
                    source = node.getSource()

                    if source.isExpressionConstantRef():
                        try:
                            unpackable = iter( source.getConstant() )
                        except TypeError:
                            return

                        unpacked = list( unpackable )
                        elements = target.getElements()

                        if len( unpacked ) == len( elements ):
                            statements = []

                            for value, element in zip( unpacked, elements ):
                                statements.append(
                                    Nodes.CPythonStatementAssignment(
                                        targets    = ( element, ),
                                        expression = Nodes.makeConstantReplacementNode(
                                            constant = value,
                                            node     = node
                                        ),
                                        source_ref = node.getSourceReference()
                                    )
                                )

                            node.replaceWith(
                                Nodes.CPythonStatementsSequence(
                                    statements = statements,
                                    source_ref = node.getSourceReference()
                                )
                            )

                            self.signalChange(
                                "new_statements",
                                node.getSourceReference(),
                                "Removed useless unpacking assignments."
                            )
                        else:
                            if len( unpacked ) > len( elements ):
                                node.replaceWith(
                                    makeRaiseExceptionReplacementStatement(
                                        statement       = node,
                                        exception_type  = "ValueError",
                                        exception_value = "too many values to unpack",
                                    )
                                )
                            elif len( unpacked ) == 1:
                                node.replaceWith(
                                    makeRaiseExceptionReplacementStatement(
                                        statement       = node,
                                        exception_type  = "ValueError",
                                        exception_value = "need more than 1 value to unpack",
                                    )
                                )
                            else:
                                node.replaceWith(
                                    makeRaiseExceptionReplacementStatement(
                                        statement       = node,
                                        exception_type  = "ValueError",
                                        exception_value = "need more than %s values to unpack" % len( unpacked ),
                                    )
                                )


                            self.signalChange(
                                "new_code",
                                node.getSourceReference(),
                                "Removed bound to fail unpacking assignments."
                            )

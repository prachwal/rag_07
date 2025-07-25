"""
Function execution handler for safe function calling.
Provides secure execution of functions called by LLM.
"""

from typing import Any, Dict

from src.tools.vector_search_tools import VectorSearchTools
from src.utils.logger import LoggerMixin


class FunctionExecutor(LoggerMixin):
    """Safe executor for LLM function calls."""

    def __init__(self, tools: VectorSearchTools):
        """Initialize function executor.

        Args:
            tools: VectorSearchTools instance with available functions
        """
        self.tools = tools
        self.function_map = {
            "search_documents": self.tools.search_documents,
            "get_document_details": self.tools.get_document_details,
        }

    async def execute_function(
        self, function_name: str, function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a function call safely with error handling.

        Args:
            function_name: Name of the function to execute
            function_args: Arguments to pass to the function

        Returns:
            Dictionary with function result or error information
        """
        try:
            # Validate function name
            if function_name not in self.function_map:
                self.log_operation(
                    "function_execution_error",
                    function_name=function_name,
                    error="unknown_function",
                )
                return {
                    "status": "error",
                    "message": f"Unknown function: {function_name}",
                    "available_functions": list(self.function_map.keys()),
                }

            # Get function
            function = self.function_map[function_name]

            # Log function execution start
            self.log_operation(
                "function_execution_started",
                function_name=function_name,
                args_keys=list(function_args.keys()),
            )

            # Execute function with provided arguments
            result = await function(**function_args)

            # Log successful execution
            self.log_operation(
                "function_execution_completed",
                function_name=function_name,
                success=result.get("status") == "success",
            )

            return result

        except TypeError as e:
            # Handle invalid arguments
            error_msg = f"Invalid arguments for {function_name}: {str(e)}"
            self.log_operation(
                "function_execution_error",
                function_name=function_name,
                error="invalid_arguments",
                error_details=str(e),
            )

            return {
                "status": "error",
                "message": error_msg,
                "function_name": function_name,
                "error_type": "invalid_arguments",
            }

        except Exception as e:
            # Handle any other execution errors
            error_msg = f"Function execution error in {function_name}: {str(e)}"
            self.log_operation(
                "function_execution_error",
                function_name=function_name,
                error="execution_failed",
                error_details=str(e),
            )

            return {
                "status": "error",
                "message": error_msg,
                "function_name": function_name,
                "error_type": "execution_failed",
            }

    def get_available_functions(self) -> Dict[str, str]:
        """Get list of available functions with descriptions.

        Returns:
            Dictionary mapping function names to descriptions
        """
        return {
            "search_documents": ("Search for relevant documents in the knowledge base"),
            "get_document_details": (
                "Get detailed information about a specific document"
            ),
        }

    def validate_function_args(
        self, function_name: str, function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate function arguments before execution.

        Args:
            function_name: Name of the function
            function_args: Arguments to validate

        Returns:
            Validation result with status and messages
        """
        validation_result = {"valid": True, "errors": [], "warnings": []}

        try:
            if function_name == "search_documents":
                # Validate search_documents arguments
                if "query" not in function_args:
                    validation_result["valid"] = False
                    validation_result["errors"].append(
                        "Missing required argument: query"
                    )
                elif not function_args["query"].strip():
                    validation_result["valid"] = False
                    validation_result["errors"].append("Query cannot be empty")

                # Check max_results bounds
                max_results = function_args.get("max_results", 5)
                if max_results < 1 or max_results > 20:
                    validation_result["warnings"].append(
                        f"max_results ({max_results}) will be clamped to 1-20"
                    )

            elif function_name == "get_document_details":
                # Validate get_document_details arguments
                if "document_id" not in function_args:
                    validation_result["valid"] = False
                    validation_result["errors"].append(
                        "Missing required argument: document_id"
                    )
                elif not function_args["document_id"].strip():
                    validation_result["valid"] = False
                    validation_result["errors"].append("document_id cannot be empty")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")

        return validation_result

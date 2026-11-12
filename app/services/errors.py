class QAServiceError(Exception):
    status_code = 500
    code = "qa_error"
    message = "The request could not be completed."


class IndexUnavailableError(QAServiceError):
    status_code = 503
    code = "index_unavailable"
    message = "The knowledge index is unavailable or empty. Run rag-ingest and try again."


class ModelCallError(QAServiceError):
    status_code = 502
    code = "model_error"
    message = "The language model could not complete the request."


class ModelTimeoutError(QAServiceError):
    status_code = 504
    code = "model_timeout"
    message = "The language model request timed out."

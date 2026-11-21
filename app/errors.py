from fastapi.responses import JSONResponse


class Problem(Exception):
    def __init__(self, code, message, status=422):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


async def response(request, error):
    return JSONResponse({'code': error.code, 'message': error.message}, status_code=error.status)

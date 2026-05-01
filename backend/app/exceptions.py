class SubLedgerError(Exception):
    status_code: int = 500
    detail_zh: str = "服务器内部错误"


class AuthenticationError(SubLedgerError):
    status_code = 401
    detail_zh = "认证失败，请重新登录"


class ForbiddenError(SubLedgerError):
    status_code = 403
    detail_zh = "无权限执行此操作"


class NotFoundError(SubLedgerError):
    status_code = 404
    detail_zh = "请求的资源不存在"


class ValidationError(SubLedgerError):
    status_code = 422
    detail_zh = "数据验证失败"


class ExchangeRateError(SubLedgerError):
    status_code = 503
    detail_zh = "汇率服务暂时不可用"
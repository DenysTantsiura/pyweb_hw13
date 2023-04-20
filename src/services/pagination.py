from pydantic import BaseModel, conint
from fastapi_pagination.bases import BaseRawParams, RawParams

class PageParams(BaseModel):
    """ Request query params for paginated API. """
    page: conint(ge=1) = 1
    size: conint(ge=1, le=100) = 10

    def to_raw_params(self) -> BaseRawParams:
        params = BaseRawParams()
        params.as_limit_offset(RawParams(limit=self.size, offset=self.size * (self.page - 1)))

        # params.as_cursor(self.size)
        return params
        # return BaseRawParams(
        #                  limit=self.size,
        #                  offset=self.size * (self.page - 1),
        #                 )


'''


class PageParams(BaseModel):
    """ Request query params for paginated API. """
    page: conint(ge=1) = 1
    size: conint(ge=1, le=100) = 10

    def to_raw_params(self) -> BaseRawParams:
        params = BaseRawParams()
        params.as_limit_offset(RawParams(limit=self.size, offset=self.size * (self.page - 1)))

        # params.as_cursor(self.size)
        return params
        # return BaseRawParams(
        #                  limit=self.size,
        #                  offset=self.size * (self.page - 1),
        #                 )
'''
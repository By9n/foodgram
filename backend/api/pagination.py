from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 4
    page_size = 6

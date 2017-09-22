class CloudManagerException(Exception):
    """An exception that cloud manager uses."""
    pass


class MasterCountChangeError(CloudManagerException):
    """Expection when request master count if different with exist one"""
    pass


class TerraformOperationFailError(CloudManagerException):
    """Exception when terraform failed to scale cloud"""
    pass

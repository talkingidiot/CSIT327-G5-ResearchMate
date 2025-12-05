from storages.backends.s3boto3 import S3Boto3Storage

class VerificationStorage(S3Boto3Storage):
    bucket_name = 'verification_documents' 
    location = ''
    file_overwrite = False
    default_acl = 'private' 
    custom_domain = False
    querystring_auth = True    
import re


def extract_city_and_country(file_path, s3_bucket_prefix):
    file_path = file_path.removeprefix(s3_bucket_prefix)
    directories = file_path.split('/')
    if re.match(r'^\d{4}$', directories[0]) is not None:  # remove the first dir with year if it exists
        directories = directories[1:]
    # format: date - order - country - city/**/jpg
    if ' - ' in directories[0]:
        parts = directories[0].split(' - ')
        return parts[-1], parts[-2]
    # format: country/city/**/jpg
    return directories[1], directories[0]

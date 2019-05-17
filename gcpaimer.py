#!/usr/bin/env python3
import argparse
import warnings
from pprint import pprint

import tqdm
from google.oauth2 import service_account
from googleapiclient import discovery

warnings.filterwarnings(
    action='ignore',
    module=r'google.auth.*'
)

def chunks(l, n):
    """Returns successive n-sized chunks from l."""
    result = []
    for i in range(0, len(l), n):
        result.append(l[i:i + n])
    return result

def main():
    parser = argparse.ArgumentParser(description='Tests all permissions for the specific GCP project.')

    parser.add_argument(
        '--creds', help='path to the service account key, if option is not provided it defaults to gcloud creds')
    parser.add_argument('--project', required=True, help='the project to test permissions on')

    args = parser.parse_args()
    resource = args.project
    if args.creds:
        credentials = service_account.Credentials.from_service_account_file(args.creds)
    else:
        credentials = None

    service = discovery.build('iam', 'v1', credentials=credentials)
    query_testable_permissions_request_body = {
        'fullResourceName': '//cloudresourcemanager.googleapis.com/projects/my-project',
        'pageSize': 1000
    }

    grantable_permissions = []
    print('Querying all testable permissions')
    while True:
        request = service.permissions().queryTestablePermissions(body=query_testable_permissions_request_body)
        response = request.execute()
        grantable_permissions.extend(response.get('permissions', []))
        if 'nextPageToken' not in response:
            break
        query_testable_permissions_request_body['pageToken'] = response['nextPageToken']

    service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

    granted_permissions = []
    print(f"Testing {len(grantable_permissions)} on project {resource}")
    with tqdm.tqdm(total=len(grantable_permissions)) as pbar:
        for chunk in chunks([p['name'] for p in grantable_permissions], 100):
            test_iam_permissions_request_body = {"permissions": chunk}
            request = service.projects().testIamPermissions(
                resource=resource, body=test_iam_permissions_request_body)
            response = request.execute()
            if response:
                granted_permissions.extend(response.get('permissions', []))
            pbar.update(len(chunk))
    pprint(granted_permissions)
    print('check https://cloud.google.com/iam/docs/permissions-reference for the reference')

if __name__ == "__main__":
    main()

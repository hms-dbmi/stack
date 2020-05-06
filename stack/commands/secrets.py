"""The secrets command."""

import os
import boto3
import json
import base64
from botocore.exceptions import ClientError

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')

headers = '''#
# THIS IS AN AUTO-GENERATED FILE CONTAINING SENSITIVE SECRETS FOR THE STACK
#
'''


class Secrets(Base):

    def run(self):

        # Get name of secret
        secret_name = Stack.get_secrets_config('name')
        try:
            # Get the secrets manager client.
            session = boto3.session.Session(profile_name=Stack.get_secrets_config('profile'))
            client = session.client('secretsmanager', region_name=Stack.get_secrets_config('region'))

            # Get the secrets
            response = client.get_secret_value(SecretId=secret_name)

            # Get values of secrets
            if 'SecretString' in response:
                secrets = json.loads(response['SecretString'])
            else:
                secrets = base64.b64decode(response['SecretBinary'])

            # Check if file exists
            path = os.path.join(Stack.get_stack_root(), '.env')
            if os.path.exists(path):

                # Prompt to overwrite
                if not self.options['--force']:
                    logger.error('(secrets) The .env secrets file already exists. Run with "-f" to overwrite.')
                    exit(0)

            # Determine how to write
            if type(secrets) is dict:
                with open(path, 'w') as f:
                    f.write(headers + '\n')
                    for key, value in secrets.items():
                        if type(value) is str:
                            f.write('{}={}\n'.format(key.upper(), value))
                        else:
                            f.write('{}={}\n'.format(key.upper(), json.dumps(value)))

            else:
                with open(path, 'w+b') as f:
                    f.write(secrets)

            logger.info('(secrets) Fetched and saved secrets to "{}"'.format(path))

        except ClientError as e:
            if e.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InternalServiceErrorException':
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                logger.error('(secrets) Error: No secret could be found for name "{}"'.format(secret_name))

        except Exception as e:
            logger.exception('Secrets error: {}'.format(e))
            exit(1)

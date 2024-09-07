import json

def lambda_handler(event, context):
    # TODO implement
    print(event, context)
    return {
        'statusCode': 200,
        'body': json.dumps("it is working")
    }


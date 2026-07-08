import json

def sanitize_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def sanitize(node):
        if isinstance(node, dict):
            # Keys to delete
            keys_to_delete = ['marketMakerAddress', 'submitted_by', 'resolvedBy', 'proxyAddress', 'address']
            for k in keys_to_delete:
                if k in node:
                    del node[k]
            for v in node.values():
                sanitize(v)
        elif isinstance(node, list):
            for item in node:
                sanitize(item)

    sanitize(data)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

if __name__ == '__main__':
    sanitize_json('gamma_response_sample.json')

import json
import sys

def handle(req):
	if req:
		# print(req)
		sys.stderr.write(req)
		json_req = json.loads(req)
		r = json_req["refer"]
		print(type(r), sys.stderr)
	else:
	    # print("empty")
	    sys.stderr.write("empty\n")

	print(type(req), sys.stderr)

	result = { "status": True }
	return result

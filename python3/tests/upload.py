# Reference: Resumable uploads over HTTP. Protocol specification
#  http://www.grid.net.ru/nginx/resumable_uploads.en.html
#
#Example 1: Request from client containing the first segment of the file
#
#POST /upload HTTP/1.1
#Host: example.com
#Content-Length: 51201
#Content-Type: application/octet-stream
#Content-Disposition: attachment; filename="big.TXT"
#X-Content-Range: bytes 0-51200/511920
#Session-ID: 1111215056 
#
#<bytes 0-51200>
#
#Example 2: Response to a request containing first segment of a file
#
#HTTP/1.1 201 Created
#Date: Thu, 02 Sep 2010 12:54:40 GMT
#Content-Length: 14
#Connection: close
#Range: 0-51200/511920
#
#0-51200/511920 
#
#Example 3: Request from client containing the last segment of the file
#
#POST /upload HTTP/1.1
#Host: example.com
#Content-Length: 51111
#Content-Type: application/octet-stream
#Content-Disposition: attachment; filename="big.TXT"
#X-Content-Range: bytes 460809-511919/511920
#Session-ID: 1111215056
#
#<bytes 460809-511919>
#
#Example 4: Response to a request containing last segment of a file
#
#HTTP/1.1 200 OK
#Date: Thu, 02 Sep 2010 12:54:43 GMT
#Content-Type: text/html
#Connection: close
#Content-Length: 2270
#
#<response body>

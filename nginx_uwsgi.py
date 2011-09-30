import os, sys, stat, socket, struct, StringIO, time, traceback
import web, web.wsgi

SERVER_PORT         = 55555
FOOT_PRINTS_PATH    = None
ERROR_LOG_PATH      = None

def parseRequest(sock):
    """
    This function receives request buffer from nginx, and then
    parses the buffer into a Python dictionary.
    """
    buf = sock.recv(4, socket.MSG_WAITALL)
    if len(buf) < 4:
        raise Exception()
    size = struct.unpack("=H", buf[1:3])[0]
    buf = sock.recv(size, socket.MSG_WAITALL)
    if len(buf) < size:
        raise Exception()

    request = {}
    i = 0
    while i < len(buf):
        size = struct.unpack("=H", buf[i:i+2])[0]
        k = buf[i+2:i+2+size]
        i = i + 2 + size
        size = struct.unpack("=H", buf[i:i+2])[0]
        v = buf[i+2:i+2+size]
        i = i + 2 + size
        request[k] = v

    if request.has_key("CONTENT_LENGTH") and \
            len(request["CONTENT_LENGTH"]) > 0:
        size = int(request["CONTENT_LENGTH"])
        data = sock.recv(size, socket.MSG_WAITALL)
        if len(data) < size:
            raise Exception()
        request["wsgi.input"] = StringIO.StringIO(data)

    request["request_log"] = {}

    return request

def nginxRunuwsgi(func):
    """
    As a listen-accept interface, this function can be
    assigned to web.wsgi.runwsgi.
    """
    if stat.S_ISSOCK(os.fstat(0)[stat.ST_MODE]):
        s_l = socket.fromfd(0, socket.AF_INET, socket.SOCK_STREAM)
        sys.stderr.close()
        try:
            if ERROR_LOG_PATH is not None:
                sys.stderr = open(ERROR_LOG_PATH, "a")
        except:
            pass
    else:
        s_l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_l.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s_l.bind( ("127.0.0.1", SERVER_PORT) )
        s_l.listen(1)

    while True:
        try:
            s_a = s_l.accept()[0]
        except:
            sys.stderr.write("Accept failed!\n")
            break;
        finally:
            sys.stderr.flush()

        try:
            request = parseRequest(s_a)
        except Exception, e:
            s_a.close()
            sys.stderr.write("Parse request failed!\n")
            sys.stderr.write(traceback.format_exc()+"\n")
            continue;
        finally:
            sys.stderr.flush()

        def nginx_start_response(status, headers):
            s_a.send("HTTP/1.1 " + status + "\r\n")
            for (k, v) in headers:
                s_a.send( "{0}: {1}\r\n".format(k, v) )
            s_a.send("\r\n")

            '''write log start'''
            if FOOT_PRINTS_PATH is not None:
                f_log = open(FOOT_PRINTS_PATH, "a")
            else:
                f_log = None

            def quote(s_in):
                s_out = ""
                for c in s_in:
                    if ord(c) <= 0x20 or ord(c) >= 0x7F or \
                            c in ("\\", "'", '"'):
                        s_out = s_out + "\\x{0:02x}".format( ord(c) )
                    else:
                        s_out = s_out + c
                return s_out

            def writeKey(k):
                f_log.write(' "')
                if request.has_key(k):
                    f_log.write( quote( str(request[k]) ) )
                f_log.write('"')

            if f_log is not None:
                f_log.write( time.strftime( '"%Y-%m-%d/%H:%M:%S"',
                    time.localtime() ) )
                f_log.write(' "' + quote(request["REMOTE_ADDR"] +
                    ":" + request["REMOTE_PORT"]) + '"')
                f_log.write(' "' + quote(status.split(" ")[0]) + '"')

                writeKey("REQUEST_METHOD")
                writeKey("REQUEST_URI")
                writeKey("HTTP_REFERER");
                writeKey("HTTP_COOKIE");
                writeKey("HTTP_USER_AGENT");
                writeKey("request_log");

                f_log.write("\n")
                f_log.close()
            '''write log end'''
            #end nginx_start_response
        
        try:
            response = func(request, nginx_start_response)
            for chunk in response:
                s_a.send(chunk)
        except Exception, e:
            s_a.close()
            sys.stderr.write("Process request failed!\n")
            sys.stderr.write(traceback.format_exc()+"\n")
            continue;
        finally:
            sys.stderr.flush()

        s_a.close()

web.wsgi.runwsgi = nginxRunuwsgi;

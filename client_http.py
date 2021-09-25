#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# System modules
import mimetypes
import re
import socket
import time
import urllib.parse
import os.path
# Internal modules
import config_srv


def data_type(file=None):
    """
    Guess the type of a file based on its filename, path or URL.
    :param file: file path
    :type file: str or None
    :return: (type/sub-type; charset=character set)
    :rtype: str or none
    """
    if file is None:
        return "text/html; charset=UTF-8"
    try:
        (type_subtype, charset) = mimetypes.guess_type(file)
        if type_subtype == "text/html":
            charset = "UTF-8"
        elif type_subtype is None:
            return None
        if charset is not None:
            return type_subtype + "; charset=" + charset
        else:
            return type_subtype + ";"
    except ImportError:
        print("Missing Import")
    except OSError:
        return None


def data_reader(file_name):
    """
    Read data of a file from the directory.
    :param file_name: Full directory of the file to read
    :type file_name: file
    :return: header and data
    :rtype: tuple
    """
    # If directory and file exists, open it, and send data
    if os.path.isfile(file_name):
        try:
            with open(file_name, "rb") as file:
                data = file.read()
                header = generate_header(200, len(data), data_type(file_name))
        except IOError:
            data = gen_data_error(500)
            header = generate_header(500, len(data), data_type(None))
    else:
        data = gen_data_error(404)
        header = generate_header(404, len(data), data_type(None))
    return header, data


def build_file_path(first_line):
    """
    Build the file directory from first line of HTTP header
    :param first_line: the first line from header
    :type first_line: str
    :return: final_path to a file, or index.html by default if not specified
    :rtype: str
    """
    # GET /index.html HTTP/1.1 -> /index.html
    file_path_on_first_line = first_line.split(" ")[1]

    # Make /index.html default directory
    default_file = 'index.html'
    default = config_srv.CONFIGURATION['Path'] + default_file

    # == no/blank directory --> index.html
    if 'HTTP' in file_path_on_first_line:
        return default

    # Cleaning path
    file_path_on_first_line_cleaned = urllib.parse.unquote(file_path_on_first_line)

    # If path include question mark, don't take the following
    if "?" in file_path_on_first_line_cleaned:
        file_path_on_first_line_cleaned = file_path_on_first_line_cleaned.split("?")[0]

    # If no file specified, open default
    if file_path_on_first_line.endswith("/"):
        final_path = config_srv.CONFIGURATION['Path'][:-1] + file_path_on_first_line_cleaned + default_file
    else:
        try:
            final_path = config_srv.CONFIGURATION['Path'][:-1] + file_path_on_first_line_cleaned
        except OSError:
            return default
    return final_path


def gen_data_error(code):
    """
    :param code: HTTP error code or OK code
    :type code: int
    :return: HTML page error code
    :rtype: basestring
    """
    if code == 200:
        return None
    error = {
        400: b"<html><body><center><h1>Error 400: Bad request error</h1></center><p>Head back to <a href=\"/\">home "
             b"page</a>.</p></body></html>",
        404: b"<html><body><center><h1>Error 404: Not found</h1></center><p>Head back to <a href=\"/\">home "
             b"page</a>.</p></body></html>",
        405: b"<html><body><center><h1>Error 405: Method not allowed</h1></center><p>Head back to <a href=\"/\">home "
             b"page</a>.</p></body></html>",
        500: b"<html><body><center><h1>Error 500: Internal server error</h1></center><p>Head back to <a "
             b"href=\"/\">home page</a>.</p></body></html>",
    }
    if code not in error:
        code = 500
    return error[code]


def generate_header(code_response, length=None, type_mime="text/html; charset=UTF-8"):
    """
    Generates a response to the request according to the response code
    :param type_mime: type and subtype of requested file
    :param length: length of the header
    :param code_response: HTTP server code
    :type code_response: int
    :return response_header = "HTTP/1.1 200 OK\r\n"\
                    "Date: ven., 24 nov. 2017 15:34:41 CET"\
                    "Server: HacheTTP"\
                    "Content-Type: text/html; charset=UTF-8"\
                    "Content-Length: 449"
    :rtype: str
    """

    code = {
        200: "200 OK",
        400: "400 BAD REQUEST",
        404: "404 NOT FOUND",
        405: "405 METHOD NOT ALLOWED",
        500: "500 INTERNAL SERVER ERROR",
    }

    date = time.strftime("%a, %d %b %Y %H:%M:%S")

    if code_response not in code:
        code_response = 500
    codeutil = code[code_response]

    # Generate response header
    response_header = "HTTP/1.1 " + codeutil + "\r\n"
    response_header += "Date: " + date + "\r\n"
    response_header += "Server: Tobi\r\n"
    response_header += "Connection: close\r\n"
    response_header += "Content-Type: " + type_mime + "\r\n"
    # Don't put Content-Length if length is null
    if length is not None:
        response_header += "Content-Length: " + str(length) + "\r\n"
    else:
        # print("/!\\ Length is None")
        pass

    response_header += "\r\n"

    return response_header


def verify_request(req):
    """
    Checks the content of the request
    :param req: requête
    :type req: str
    :return: HTTP error code
    :rtype: int
    """
    # If there is a fail, return 500 error code
    request = 500

    try:
        # Cutting the big block in lines
        header = req.split("\n")
        # Insulation of the first line
        first_line = header[0].split(" ")
    except OSError:
        print(request, "Internal server error.")
        return request
    # test the content of the first line
    if len(first_line) == 3:
        method = first_line[0]  # GET POST ...
        global directory
        directory = first_line[1]  # /index.html
        protocol_with_version = first_line[2].split("/")  # HTTP 1.1
        protocol = protocol_with_version[0]  # HTTP
        version = protocol_with_version[1]  # 1.1
        if method == "GET" and protocol == "HTTP" and (version == "1.1\r" or version == "1.0\r"):
            # test the rest of the header content
            for elt in header[1:]:
                if re.match("^[A-Za-z- ]*[:].*", elt) or elt == "\r" or elt == "":
                    request = 200
                else:
                    request = 400
                    return request
        else:
            request = 405
    else:
        request = 400

    return request


def read_request(sock_client):
    """
    Get the user request
    :param sock_client: socket representing the connection with the client
    :type sock_client: socket
    :return: The request in str
    :rtype: str
    """
    stop = False
    data = b""
    buf = b""
    try:
        while not stop:
            try:
                buf = sock_client.recv(1024)
                data += buf
                if buf.endswith(b"\r\n\r\n"):
                    stop = True
            except Exception as e:
                print(e)
                return None
    except OSError:
        return None

    return data.decode("utf-8")


def client_processing(sock_client):
    """
    :param sock_client: socket representing the connection with the client
    :return: None
    :rtype: None
    """
    print("Processing the client's request.")
    request = read_request(sock_client)
    if request is None:
        return None

    code = verify_request(request)
    if code == 200:
        path = build_file_path(request.split("\r\n")[0])
        (header, data) = data_reader(path)
    else:
        length = len(directory)
        header = generate_header(code, length)
        data = gen_data_error(code)

    try:
        data_to_send = header.encode('utf-8') + data
        sock_client.sendall(data_to_send)
        print("Client request done successfully.")
    except socket.error:
        print("Socket Error")

    return None


def main():
    # Test

    # ----- verify_request()

    header = 'GET /file HTTP/1.1\r\n'
    core = 'Host: 127.0.0.1:8000\r\n' \
           'Connection: keep-alive\r\n' \
           'Cache-Control: max-age=0\r\n' \
           'Upgrade-Insecure-Requests: 1\r\n' \
           'DNT: 1\r\n' \
           'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
           'Chrome/80.0.3987.132 Safari/537.36\r\n' \
           'Sec-Fetch-Dest: document\r\n' \
           'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,' \
           'application/signed-exchange;v=b3;q=0.9\r\n' \
           'Sec-Fetch-Site: cross-site\r\n' \
           'Sec-Fetch-Mode: navigate\r\n' \
           'Accept-Encoding: gzip, deflate, br\r\n' \
           'Accept-Language: en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7\r\n'

    # PATH OK
    request = 'GET /src/index.html HTTP/1.1\r\n' + core
    assert verify_request(request) == 200

    # ADVANCED OK PATH
    request = 'GET /doc/doc%20en%20fran%C3%A7ais?=BLA/ HTTP/1.1\r\n' + core
    assert verify_request(request) == 200

    # WRONG METHOD
    request = 'POST /file HTTP/1.1\r\n' + core
    assert verify_request(request) == 405

    # WRONG PROTOCOL
    request = 'GET /file HTTPS/1.1\r\n' + core
    assert verify_request(request) == 405

    # WRONG PROTOCOL VERSION
    request = 'GET /file HTTP/2.0\r\n' + core
    assert verify_request(request) == 405

    # WRONG NUMBER OF ARGS
    request = 'GET HTTP/1.1\r\n' + core
    assert verify_request(request) == 400

    # MISSING SPACE
    request = 'GET/file HTTP/1.1\r\n' + core
    assert verify_request(request) == 400

    # DIGIT BEFORE COLON Connection -> Connecti0n
    request = header + 'Host: 127.0.0.1:8000\r\n' \
                       'Connecti0n: keep-alive\r\n' \
                       'Cache-Control: max-age=0\r\n' \
                       'Upgrade-Insecure-Requests: 1\r\n' \
                       'DNT: 1\r\n' \
                       'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                       'Chrome/80.0.3987.132 Safari/537.36\r\n' \
                       'Sec-Fetch-Dest: document\r\n' \
                       'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,' \
                       '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\r\n' \
                       'Sec-Fetch-Site: cross-site\r\n' \
                       'Sec-Fetch-Mode: navigate\r\n' \
                       'Accept-Encoding: gzip, deflate, br\r\n' \
                       'Accept-Language: en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7\r\n'
    assert verify_request(request) == 400

    # COLONS ";" INSTEAD OF A SPACE SEMI COLON ":"
    request = header + 'Host: 127.0.0.1:8000\r\n' \
                       'Connection: keep-alive\r\n' \
                       'Cache-Control; max-age=0\r\n' \
                       'Upgrade-Insecure-Requests: 1\r\n' \
                       'DNT: 1\r\n' \
                       'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                       'Chrome/80.0.3987.132 Safari/537.36\r\n' \
                       'Sec-Fetch-Dest: document\r\n' \
                       'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,' \
                       '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\r\n' \
                       'Sec-Fetch-Site: cross-site\r\n' \
                       'Sec-Fetch-Mode: navigate\r\n' \
                       'Accept-Encoding: gzip, deflate, br\r\n' \
                       'Accept-Language: en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7\r\n'
    assert verify_request(request) == 400
    print("Test verify_request OK")

    # ----- generate_header()

    code = {200: "200 OK", 400: "400 BAD REQUEST", 404: "404 NOT FOUND", 405: "405 METHOD NOT ALLOWED",
            500: "500 INTERNAL SERVER ERROR"}

    try:
        # CORRECT
        assert generate_header(200, 128) == "HTTP/1.1 " + code[200] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" + "Connection: close\r\n" + "Content-Type: " + \
            "text/html; charset=UTF-8" + "\r\n" + "Content-Length: " + str(128) + "\r\n\r\n"
        # CORRECT with length = None
        assert generate_header(200, None) == "HTTP/1.1 " + code[200] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" + "Connection: close" + "\r\n" + \
            "Content-Type: " + "text/html; charset=UTF-8" + "\r\n\r\n"
        # CORRECT but no length
        assert generate_header(200) == "HTTP/1.1 " + code[200] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" + "Connection: close" + "\r\n" + \
            "Content-Type: " + "text/html; charset=UTF-8" + "\r\n" + "\r\n"
        # ERROR CODE 400 with correct length
        assert generate_header(400, 128) == "HTTP/1.1 " + code[400] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" + "Connection: close\r\n" + "Content-Type: " + \
            "text/html; charset=UTF-8" + "\r\n" + "Content-Length: " + str(128) + "\r\n\r\n"
        # ERROR CODE 404 with correct length
        assert generate_header(404, 128) == "HTTP/1.1 " + code[404] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" + "Connection: close\r\n" + "Content-Type: " + \
            "text/html; charset=UTF-8" + "\r\n" + "Content-Length: " + str(128) + "\r\n\r\n"
        # ERROR CODE 405 with correct length
        assert generate_header(405, 128) == "HTTP/1.1 " + code[405] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" \
            + "Connection: close\r\n" + "Content-Type: " + "text/html; charset=UTF-8" + "\r\n" + \
            "Content-Length: " + str(128) + "\r\n\r\n"
        # ERROR CODE 500 with correct length
        assert generate_header(500, 128) == "HTTP/1.1 " + code[500] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" \
            + "Connection: close\r\n" + "Content-Type: " + "text/html; charset=UTF-8" + "\r\n" + "Content-Length: " + \
            str(128) + "\r\n\r\n"
        # INCORRECT ERROR CODE with correct length
        assert generate_header(-399, 128) == "HTTP/1.1 " + code[500] + "\r\n" + "Date: " + time.strftime(
            "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" \
            + "Connection: close\r\n" + "Content-Type: " + "text/html; charset=UTF-8" + "\r\n" + \
            "Content-Length: " + str(128) + "\r\n\r\n"
    except AssertionError:
        print("Test generate_header ERROR")
    print("Test generate_header OK")

    # ----- gen_data_error()

    try:
        # CORRECT : CODE 200
        assert gen_data_error(200) is None
        # CODE 400
        assert gen_data_error(
            400) == b'<html><body><center><h1>Error 400: Bad request error</h1></center><p>Head back to <a href="/">home page</a>.</p></body></html>'
        # CODE 404
        assert gen_data_error(
            404) == b'<html><body><center><h1>Error 404: Not found</h1></center><p>Head back to <a href="/">home page</a>.</p></body></html>'
        # CODE 405
        assert gen_data_error(
            405) == b'<html><body><center><h1>Error 405: Method not allowed</h1></center><p>Head back to <a href="/">home page</a>.</p></body></html>'
        # CODE 500
        assert gen_data_error(
            500) == b'<html><body><center><h1>Error 500: Internal server error</h1></center><p>Head back to <a href="/">home page</a>.</p></body></html>'
    except AssertionError:
        print("Test gen_data_error ERROR")
    print("Test gen_data_error OK")

    # ----- build_file_path()

    try:
        # NO PATH SPECIFIED IN URL
        assert build_file_path("GET HTTP/1.1\r\n") == config_srv.CONFIGURATION['Path'] + 'index.html'
        assert build_file_path("GET / HTTP/1.1\r\n") == config_srv.CONFIGURATION['Path'] + 'index.html'

        # SIMPLE PATH
        assert build_file_path("GET /Iamafile.html HTTP/1.1\r\n") == config_srv.CONFIGURATION[
            'Path'] + 'Iamafile.html'

        # ADVANCED PATH
        assert build_file_path("GET /path%20space.file HTTP/1.1\r\n") == config_srv.CONFIGURATION[
            'Path'] + 'path space.file'
        assert build_file_path("GET /path.html?=contenu HTTP/1.1\r\n") == config_srv.CONFIGURATION[
            'Path'] + 'path.html'
        assert build_file_path("GET /doc/doc%20en%20fran%C3%A7ais/ HTTP / 1.1\r\n") == \
            config_srv.CONFIGURATION['Path'] + 'doc/doc en français/index.html'

    except AssertionError:
        print("Test build_file_path ERROR")
    print("Test build_file_path OK")

    # ----- data_reader()

    # FILE FOUND
    first_line = "GET / HTTP/1.1"
    path = build_file_path(first_line)
    size = os.path.getsize(path)
    expected_response_header = "HTTP/1.1 " + code[200] + "\r\n" + "Date: " + time.strftime(
        "%a, %d %b %Y %H:%M:%S") + "\r\n" + "Server: Tobi" + "\r\n" + "Connection: close" + "\r\n" + \
        "Content-Type: " + "text/html; charset=UTF-8" + "\r\n" + "Content-Length: " + str(size) + "\r\n\r\n"
    expected_response_data = b'<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>test</title></head><body><div style="text-align: center;"><h1>TEST PAGE</h1><h2>I think it\'s working...</h2></div></body></html>'
    try:
        assert data_reader(path) == (expected_response_header, expected_response_data)
    except AssertionError:
        print("POSSIBLE ERROR 1 : check date time between read data and expect header\r\n")
        print(data_reader(path)[0])
        print(expected_response_header)

    # FILE NOT FOUND
    first_line = "GET /thisisnotafile.html HTTP/1.1"
    path = build_file_path(first_line)
    size = len(gen_data_error(404))
    expected_response_header = "HTTP/1.1 " + code[404] + "\r\n" + "Date: " + time.strftime("%a, %d %b %Y %H:%M:%S") + \
                               "\r\n" + "Server: Tobi" + "\r\n" + "Connection: close" + "\r\n" + "Content-Type: " + \
                               "text/html; charset=UTF-8" + "\r\n" + "Content-Length: " + str(size) + "\r\n\r\n"
    expected_response_data = gen_data_error(404)
    try:
        assert data_reader(path) == (expected_response_header, expected_response_data)
    except AssertionError:
        print("POSSIBLE ERROR 2 : check date time between read data and expect header\r\n")
        print(expected_response_header)
        print(data_reader(path)[0])

    # #  ANY READING PROBLEMS like no perms on a file requested first_line = "GET /no_perms HTTP/1.1" path =
    # build_file_path(first_line) size = len(gen_data_error(500)) expected_response_header = "HTTP/1.1 " + code[500]
    # + "\r\n" + "Date: " + time.strftime("%a, %d %b %Y %H:%M:%S") + \ "\r\n" + "Server: Tobi" + "\r\n" +
    # "Connection: close" + "\r\n" + "Content-Type: " + \ "text/html; charset=UTF-8" + "\r\n" + "Content-Length: " +
    # str(size) + "\r\n\r\n" expected_response_data = gen_data_error(500) assert data_reader(path) == (
    # expected_response_header, expected_response_data)

    print("Test data_reader OK")

    # ----- data_type()

    try:
        # HTML file
        assert data_type("/index.html") == "text/html; charset=UTF-8"
        # CSS file
        assert data_type("/index.css") == "text/css;"
        # JPG file
        assert data_type("/test/py.jpg") == "image/jpeg;"
        # PNG file
        assert data_type("/test/py.png") == "image/png;"
        # PDF file
        assert data_type("/test/py.pdf") == "application/pdf;"
        # WRONG
        assert data_type("/test/test.0") is None
    except AssertionError:
        print("Test data_type ERROR")
    print("Test data_type OK")

    return


if __name__ == "__main__":
    main()

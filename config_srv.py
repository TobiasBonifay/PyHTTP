#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# System modules
import os
import threading

CONFIGURATION = {'Host': '', 'Port': 8000, 'Path': os.getcwd() + '/html/'}

lock = threading.Lock()


def get_config(key):
    """
    return the specific config key value
    """
    lock.acquire()
    try:
        key_val = CONFIGURATION[key]
    except KeyError:
        key_val = None
    except OSError:
        key_val = None
        print("Fatal Error")
    finally:
        # Always called, even if exception is raised in try block
        lock.release()
    return key_val


def set_config(key, value):
    """
    change the specific config key value
    """
    lock.acquire()
    try:
        if key not in CONFIGURATION:
            return False
        if type(value) is not str and type(value) is not int:
            return False
        CONFIGURATION[key] = value
    except KeyError:
        return False
    except OSError:
        print("Fatal Error")
        return False
    finally:
        # Always called, even if exception is raised in try block
        lock.release()
    return True


def main():

    # Test get_config function working with thread
    def test_get_config(key, expected_res):
        assert get_config(key) == expected_res
        return None

    def test_threads_get(key, expected_res, nb_threads):
        try:
            t = []  # t : thread
            for i in range(nb_threads):
                t.append(threading.Thread(target=test_get_config, args=(key, expected_result)))
                t[i].start()
            for i in range(len(t)):
                t[i].join()
        except AssertionError:
            return False
        except OSError:
            print("OS Error")
            return False
        return True

    # Test set_config function working with thread
    def test_set_config(key, value, expected_res):
        assert set_config(key, value) == expected_res
        return None

    def test_threads_set(key, value, expected_res, nb_threads):
        try:
            t = []  # t : thread
            for i in range(nb_threads):
                if type(value) is int:
                    value += 1
                t.append(threading.Thread(target=test_set_config, args=(key, value, expected_result)))
                t[i].start()
            for i in range(len(t)):
                t[i].join()
            test_get_config(key, value)
        except AssertionError:
            return False
        except OSError:
            print("OS Error")
            return False
        return True

    # ----- get_config() ----- #

    expected_result = ""
    # Correct mono-thread
    assert test_threads_get("Host", expected_result, 1) is True

    # Correct mono-thread bis
    expected_result = 8000
    assert test_threads_get("Port", expected_result, 1) is True

    # Correct key 10 threads
    expected_result = os.getcwd() + "/html/"
    assert test_threads_get("Path", expected_result, 10) is True

    expected_result = None
    # Incorrect key mono-thread
    assert test_threads_get("HostInEnglish", expected_result, 1) is True

    # Incorrect key type mono-thread
    assert test_threads_get(None, expected_result, 1) is True

    # Incorrect key 10 thread
    assert test_threads_get("NotThePort", expected_result, 10) is True

    print("Test get_config OK")

    # ----- set_config() ----- #

    expected_result = True
    # Correct mono-thread
    assert test_threads_set("Host", "localhost", expected_result, 1) is True

    # Correct mono-thread bis
    assert test_threads_set("Port", 8000, expected_result, 1) is True

    # Correct 10 threads
    assert test_threads_set("Path", "/this_is_a_directory", expected_result, 10) is True

    expected_result = False
    # Incorrect key mono-thread
    assert test_threads_set("HostInEnglish", "localhost", expected_result, 1) is False

    # Incorrect key type mono-thread
    assert test_threads_set(None, "localhost", expected_result, 1) is False

    # Incorrect key 10 threads
    assert test_threads_set("IncorrectPortName", 8000, expected_result, 10) is False

    # Incorrect value mono-thread
    assert test_threads_set("Host", ("quack", "hey"), expected_result, 1) is False

    # Incorrect value 10 threads
    assert test_threads_set("Port", None, expected_result, 10) is False

    print("Test set_config OK")


if __name__ == "__main__":
    main()

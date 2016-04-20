#!/usr/bin/env php
<?php
defined('USAGE')
|| define('USAGE', basename($argv[0]) . " - url encoder/decoder" . PHP_EOL .
    "USAGE: " . basename($argv[0]) . " [OPTION] [STRING]" . PHP_EOL . PHP_EOL .
    "Possible options:" . PHP_EOL .
    "\t-d  -  Decode a urlencoded string" . PHP_EOL .
    "\t-e  -  Encode a normalized string" . PHP_EOL .
    "\t-h  -  Print this text and exit" . PHP_EOL . PHP_EOL .
    "Example call:\t" . basename($argv[0]) . " -e 'This is normalized string@command line%with#special symbols'" . PHP_EOL .
    "Output:\t\tThis+is+normalized+string%40command+line%25with%23special+symbols" . PHP_EOL);

if ($argc <= 1) {
    echo USAGE;
    exit(1);
} elseif ($argc > 3) {
    echo USAGE;
    exit(1);
} else {
    if ($argv[1] == '-e' && isset($argv[2])) {
        echo "\033[1;33m" . PHP_EOL . urlencode($argv[2]) . "\033[0m" . PHP_EOL . PHP_EOL;
        exit(0);
    } elseif ($argv[1] == '-d' && isset($argv[2])) {
        if (preg_match("/^((.*)&(.*)){1,}$/", $argv[2])) {
            // TODO: add array elements support
            echo "\n\033[32m{" . PHP_EOL . rtrim(preg_replace("/(.*)=(.*)/", "\t\"$1\": \"$2\",", preg_replace("/&/", "\n", urldecode($argv[2]))), ',') . "\n}\033[0m" . PHP_EOL . PHP_EOL;
        } else {
            echo "\033[32m" . PHP_EOL . urldecode($argv[2]) . "\033[0m" . PHP_EOL . PHP_EOL;
        }
        exit(0);
    } elseif ($argv[1] == '-v') {
        echo USAGE;
        exit(0);
    } else {
        echo "\033[31mInvalid arguments\033[0m" . PHP_EOL;
        echo USAGE;
        exit(2);
    }
}
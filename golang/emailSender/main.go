package main

import (
	"fmt"
	"os"
	"path/filepath"
	"io/ioutil"
	"crypto/tls"
	"strings"
	"errors"
)

import "gopkg.in/gomail.v2"
import "gopkg.in/alecthomas/kingpin.v2"
import "gopkg.in/yaml.v2"

var (
	to = kingpin.Flag("to", "Main receipients list").Required().Short('t').String()
	copy = kingpin.Flag("copy", "Copy receipients list").Short('c').String()
	subject = kingpin.Flag("subject", "subject text").Required().Short('s').String()
	body = kingpin.Flag("body", "Message body").Required().Short('b').String()
	attachment = kingpin.Flag("attachment", "File to attach").Short('a').ExistingFiles()
	config = kingpin.Flag("config-file", "Mail server config file").Required().ExistingFile()
	config_section = kingpin.Flag("config-section", "Config file section to use").Default("mailserver").String()
	//TODO::FLags to supported in future
	// bcc = kingpin.Flag("bcc", "Secret receipients list").Short('B').String()
	// retry = kingpin.Flag("retry", "number of retries to send mail").Short('r').Default("1").Uint8()
	// verbose = kingpin.Flag("verbose", "Turn on verbosity").Short('v').Bool()
	// compress = kingpin.Flag("compress", "Compress the attachment(s)").Bool()
)

type Config struct {
	Host      string `yaml:"host"`
	Port      int    `yaml:"port"`
	User      string `yaml:"username"`
	Password  string `yaml:"password"`
	From      string `yaml:"from"`
	FromName  string `yaml:"from_name"`
	Debug     bool   `yaml:"debug"`
	Ssl       bool   `yaml:"ssl"`
	LocalName string `yaml:"localname"`
}


func (c *Config) getFromaddress() string {
	if c.FromName == "" {
		return c.From
	}
	return c.FromName + "<" + c.From + ">"
}

type Cfg map[string]Config

func (c Cfg) getSection(s string) (Config, error) {
	if val, ok := c[s]; ok {
		h, err := os.Hostname()
		if err != nil {
			return Config{}, err
		}
		val.LocalName = h
		return val, nil
	}
	return Config{}, errors.New(fmt.Sprintf("Unknow config section: %s", s))
}

func getMessageBody(b string) (string, error) {
	if _path, err := filepath.Abs(b); err == nil {
		if _, err := os.Stat(_path); err == nil {
			f, err := ioutil.ReadFile(_path);
			if err != nil {
				fmt.Println("Failed to read file: ", err.Error())
				return "", err
			}
			return fmt.Sprintf("%s", f), nil	
		}
	}
	return b, nil
}

func init() {
	kingpin.CommandLine.HelpFlag.Short('h')
	kingpin.Parse()
}

func Splitter(s string, splits string) []string {
	m := make(map[rune]int)
	for _, r := range splits {
		m[r] = 1
	}

	splitter := func(r rune) bool {
		return m[r] == 1
	}

	return strings.FieldsFunc(s, splitter)
}

func prepareAddresses(addrs string) []string {
	return Splitter(addrs, ",")
}

func getAbsPath(files *[]string) *[]string {
	target := make([]string, len(*files))
	for idx, f := range *files {
		target[idx], _ = filepath.Abs(f)
	}
	return &target
}

func main() {

	var cfg Cfg

	_config, err := filepath.Abs(*config)

	if err != nil {
		fmt.Println(err.Error())
	}

	reader, _ := os.Open(_config)
	buf, _ := ioutil.ReadAll(reader)

	if err := yaml.Unmarshal(buf, &cfg); err != nil {
		fmt.Println(err.Error())
	}

	_cfg, err := cfg.getSection(*config_section)
	if err != nil {
		fmt.Println(err.Error())
		return
	}
	
	messageBody, err := getMessageBody(*body)

	message := gomail.NewMessage()
	message.SetHeader("From", _cfg.getFromaddress())
	message.SetHeader("To", prepareAddresses(*to)...)
	message.SetHeader("Cc", prepareAddresses(*copy)...)
	message.SetHeader("Subject", *subject)
	message.SetBody("text/html", messageBody)

	attachment = getAbsPath(attachment)

	for _, a := range *attachment {
		message.Attach(a)
	}

	dialer := gomail.NewDialer(_cfg.Host, _cfg.Port, _cfg.User, _cfg.Password)
	//>_<
	dialer.LocalName = _cfg.LocalName
	dialer.TLSConfig = &tls.Config{ServerName: _cfg.Host}
	dialer.SSL = false

	if err != nil {
		fmt.Println("Failed to create dialer to SMTP server", err.Error())
		return
	}

	if err := dialer.DialAndSend(message); err != nil {
		fmt.Println("Failed to send message", err.Error())
	}
}

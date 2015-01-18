#!/usr/bin/env python

from flask import Flask, request, send_from_directory, render_template
import os
import sys
import subprocess
import yaml
import glob
import shutil
import hmac
import hashlib

from config import secret

app = Flask(__name__)
# app.debug = False

if not os.path.exists("/tmp/ahdoc"):
    os.mkdir("/tmp/ahdoc/")
    os.mkdir("/tmp/ahdoc/git")
    os.mkdir("/tmp/ahdoc/doc")
    os.mkdir("/tmp/ahdoc/tmp")

def repo_clean(name):
    if os.path.exists("/tmp/ahdoc/git/" + name):
        shutil.rmtree("/tmp/ahdoc/git/" + name)
    if os.path.exists("/tmp/ahdoc/tmp/" + name):
        shutil.rmtree("/tmp/ahdoc/tmp/" + name)

def repo_clone(name):
    repo_clean(name)
    gitname = "/tmp/ahdoc/git/" + name
    docname = "/tmp/ahdoc/doc/" + name
    tmpname = "/tmp/ahdoc/tmp/" + name
    if not os.path.exists("/tmp/ahdoc/tmp/" + name.split("/")[0]):
        os.mkdir("/tmp/ahdoc/tmp/" + name.split("/")[0])
    ret = subprocess.call(["git", "clone", "--depth", "1",
                           "https://github.com/" + name + ".git",
                           gitname])
    if ret != 0:
        repo_clean(name)
        return "clone failed", 400
    data = None
    if not os.path.isfile(gitname + "/.ahdoc.yml"):
        repo_clean(name)
        return "no .ahdoc.yml", 400
    with open(gitname + "/.ahdoc.yml") as f:
        try:
            data = yaml.load(f.read())
        except yaml.YAMLError as ex:
            repo_clean(name)
            return "yaml error", 400
    print(data)
    ret = subprocess.call(["headerdoc2html", "-j" if data["javadoc"] else "",
                           "-o", tmpname, gitname + "/" + data["path"]])
    if ret != 0:
        repo_clean(name)
        return "headerdoc2html failed", 400
    ret = subprocess.call(["gatherheaderdoc", tmpname, "index.html"])
    if ret != 0:
        repo_clean(name)
        return "gatherheaderdoc failed", 400
    if  os.path.exists(docname):
        shutil.rmtree(docname)
    shutil.copytree(tmpname, docname)
    return "true", 200


@app.route("/", methods=["GET", "POST"], defaults={"path": ""})
@app.route("/<path:path>")
def hook(path):
    if request.method == "POST":
        if "X-Hub-Signature" not in request.headers:
            return "no hub", 400
        gh = request.headers["X-Hub-Signature"].split("sha1=")[1]
        us = hmac.new(secret, request.data, hashlib.sha1).hexdigest()
        if gh != us:
            print("hash mismatch {} {}".format(gh, us))
            return "hash mismatch", 400
        data = request.get_json()
        name = data["repository"]["full_name"]
        if ".." in name:
            return "nice try", 400
        respo = repo_clone(name)
        print(respo[0])
        return respo
    if path == "":
        return render_template("index.html",
                               docs=map(lambda x: x.split("/tmp/ahdoc/doc/")[1],
                                        glob.glob("/tmp/ahdoc/doc/*/*")))
    elif path == "style.css":
        return app.send_static_file("style.css")
    else:
        path = path.replace("..", "")
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if os.path.isfile(path):
            return send_from_directory("/tmp/ahdoc/doc/", path)
        else:
            return render_template("error.html", code=404), 404

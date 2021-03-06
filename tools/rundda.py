#!/bin/env python

import argparse
import json

import yaml

parser = argparse.ArgumentParser(description='Run a DDA object')
parser.add_argument('object_name', metavar='OBJECT_NAME', type=str, help='name of the object')
parser.add_argument('-m', dest='module', metavar='MODULE_NAME', type=str, help='module to load', nargs='+', action='append', default=[])
parser.add_argument('-a', dest='assume', metavar='ASSUME', type=str, help='...', nargs='+', action='append', default=[])
parser.add_argument('-j', dest='json',  help='...',action='store_true', default=False)
parser.add_argument('-J', dest='serialize_json',  help='...',action='store_true', default=False)
parser.add_argument('-i', dest='inject', metavar='INJECT_JSON', type=str, help='json filename to inject', nargs='+', action='append', default=[])
parser.add_argument('-t', dest='tar',  help='...',action='store_true', default=False)
parser.add_argument('-q', dest='quiet',  help='...',action='store_true', default=False)
parser.add_argument('-s', dest='silent',  help='...',action='store_true', default=False)
parser.add_argument('-v', dest='verbose',  help='...',action='store_true', default=False)
parser.add_argument('-V', dest='very_verbose',  help='...',action='store_true', default=False)
parser.add_argument('-x', dest='failsafe',  help='...',action='store_true', default=False)
parser.add_argument('-c', dest='cachelink',  help='...',action='store_true', default=False)
parser.add_argument('-f', dest='force_run', metavar='ANALYSISNAME', type=str, help='analysis to run', nargs='+', action='append', default=[])
parser.add_argument('-F', dest='force_produce', metavar='ANALYSISNAME', type=str, help='analysis to run', nargs='+', action='append', default=[])
#parser.add_argument('-v', dest='verbose', metavar='ANALYSISNAME', type=str, help='analysis to verify only', nargs='+', action='append', default=[])
parser.add_argument('-d', dest='disable_run', metavar='ANALYSISNAME', type=str, help='analysis to disable run', nargs='+', action='append', default=[])

args = parser.parse_args()

print args.module

from dataanalysis import core, importing
import dataanalysis.printhook

if args.verbose:
    print "will be chatty"
    dataanalysis.printhook.global_log_enabled=True
    dataanalysis.printhook.global_fancy_output=True
    dataanalysis.printhook.global_permissive_output=True
else:
    dataanalysis.printhook.global_log_enabled=False
    dataanalysis.printhook.global_fancy_output=False

if args.failsafe:
    print "will be chatty"
    dataanalysis.printhook.global_log_enabled=True
    dataanalysis.printhook.global_fancy_output=False
    dataanalysis.printhook.global_permissive_output=True


if args.quiet:
    print "will be quiet"
    dataanalysis.printhook.LogStream(None, lambda x: set(x) & set(['top', 'main']))
else:
    print "will not be quiet"
    dataanalysis.printhook.LogStream(None, lambda x:True)

if args.very_verbose:
    dataanalysis.printhook.global_permissive_output=True

modules=[m[0] for m in args.module]

import sys

for m in modules:
    print "importing",m

    sys.path.append(".")
    module,name= importing.load_by_name(m)
    globals()[name]=module



if len(args.assume)>0:
    assumptions = ",".join([a[0] for a in args.assume])
    print assumptions
    core.AnalysisFactory.WhatIfCopy('commandline', eval(assumptions))

A= core.AnalysisFactory[args.object_name]()

print A

for a in args.force_run:
    print "force run",a
    try:
        b= core.AnalysisFactory[a[0]]()
        b.__class__.cached=False
    except: # oh now!
        pass

for a in args.force_produce:
    print "force produce",a
    try:
        b= core.AnalysisFactory[a[0]]()
        b.__class__.read_caches=[]
    except: # oh now!
        pass

for a in args.disable_run:
    print "disable run",a
    b= core.AnalysisFactory[a[0]]()
    b.__class__.produce_disabled=True

for inj_fn, in args.inject:
    print("injecting from",inj_fn)
    inj_content=json.load(open(inj_fn))

    core.AnalysisFactory.inject_serialization(inj_content)

try:
    A.process(output_required=True)
except dataanalysis.UnhandledAnalysisException as e:
    yaml.dump(
              dict(
                  exception_type="node",
                  analysis_node_name=e.argdict['requested_by'],
                  requested_by=e.argdict['requested_by'],
                  main_log=e.argdict['main_log'],
                  traceback=e.argdict['tb'],
                ),
              open("exception.yaml","w"),
              default_flow_style=False,
        )
    raise
except Exception as e:
    print("graph exception",e)
    yaml.dump(
        dict(
            exception_type="graph",
            exception=repr(e),
        ),
        open("exception.yaml", "w"),
        default_flow_style=False,
    )
    raise


if args.json:
    print "will dump serialization to json"
    json.dump(A.export_data(embed_datafiles=True,verify_jsonifiable=True),open("object_data.json","w"), sort_keys=True,
                      indent=4, separators=(',', ': '))

if args.serialize_json:
    fn = A.get_factory_name() + "_data.json"
    json.dump(A.serialize(embed_datafiles=True, verify_jsonifiable=True), open(fn, "w"),
              sort_keys=True,
              indent=4, separators=(',', ': '))

if args.tar:
    print "will tar cache"
    print A._da_cached_path

if args.cachelink:
    if hasattr(A,'_da_cached_pathes'):
        print "will note cache link"
        open("object_url.txt","w").write("".join([args.object_name+" "+dcp+"\n" for dcp in A._da_cached_pathes]))



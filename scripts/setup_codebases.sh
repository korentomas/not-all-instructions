#!/bin/bash
set -e
cd "$(dirname "$0")/../data"
mkdir -p codebases
[ -d codebases/bambi ]       || git clone --depth 1 https://github.com/bambinos/bambi.git codebases/bambi
[ -d codebases/arviz-stats ] || git clone --depth 1 https://github.com/arviz-devs/arviz-stats.git codebases/arviz-stats
[ -d codebases/pymc ]        || git clone --depth 1 https://github.com/pymc-devs/pymc.git codebases/pymc
echo "Codebases ready in data/codebases/"

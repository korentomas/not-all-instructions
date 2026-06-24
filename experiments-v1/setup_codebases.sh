#!/bin/bash
set -e
cd "$(dirname "$0")"
mkdir -p codebases

echo "Cloning Bambi..."
[ -d codebases/bambi ] || git clone --depth 1 https://github.com/bambinos/bambi.git codebases/bambi

echo "Cloning ArviZ base..."
[ -d codebases/arviz-base ] || git clone --depth 1 https://github.com/arviz-devs/arviz-base.git codebases/arviz-base

echo "Cloning ArviZ stats..."
[ -d codebases/arviz-stats ] || git clone --depth 1 https://github.com/arviz-devs/arviz-stats.git codebases/arviz-stats

echo "Cloning PyMC..."
[ -d codebases/pymc ] || git clone --depth 1 https://github.com/pymc-devs/pymc.git codebases/pymc

echo "Done. Codebases ready in experiments/codebases/"

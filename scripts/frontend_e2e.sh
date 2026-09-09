#!/bin/bash
set -e
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use v22.23.2 > /dev/null
cd ~/ecommerce_project/frontend
npm run test:e2e 2>&1 | tail -25

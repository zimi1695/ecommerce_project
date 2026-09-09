#!/bin/bash
set -e
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use v22.23.2 > /dev/null
cd ~/ecommerce_project/frontend
npm ci 2>&1 | tail -2
npx prettier --write src/mocks/data.ts 2>&1 | tail -1
npm run check 2>&1 | tail -12

#!/bin/sh
# Replace PORT in nginx config with Railway's PORT env var
sed -i "s/\${PORT:-80}/$PORT/g" /etc/nginx/conf.d/default.conf
# Start nginx
nginx -g "daemon off;"


#!/usr/bin/env bash
#
# generate_certs.sh
#
# Generates a test PKI certificate chain for mTLS between an MCP client
# (e.g., NOS orchestrator) and an MCP server (e.g., vendor knowledge agent).
#
# Chain: Root CA -> Intermediate CA -> Client Cert + Server Cert
#
# Output directory: ../certs/
#
# WARNING: These are self-signed test certificates. Do not use in production.
# In production, use your organization's PKI or a trusted CA.

set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")/../certs" && pwd)"
mkdir -p "$CERT_DIR"

DAYS_VALID=365
RSA_BITS=4096
COUNTRY="US"
STATE="North Carolina"
ORG="MCP Tutorial"

echo "Generating certificates in: $CERT_DIR"
echo "============================================"

# --- Root CA ---
echo "[1/5] Generating Root CA..."
openssl req -x509 -newkey rsa:$RSA_BITS -nodes \
  -keyout "$CERT_DIR/root_ca.key" \
  -out "$CERT_DIR/root_ca.crt" \
  -days $DAYS_VALID \
  -subj "/C=$COUNTRY/ST=$STATE/O=$ORG/CN=MCP Tutorial Root CA"

# --- Intermediate CA ---
echo "[2/5] Generating Intermediate CA..."
openssl req -newkey rsa:$RSA_BITS -nodes \
  -keyout "$CERT_DIR/intermediate_ca.key" \
  -out "$CERT_DIR/intermediate_ca.csr" \
  -subj "/C=$COUNTRY/ST=$STATE/O=$ORG/CN=MCP Tutorial Intermediate CA"

openssl x509 -req -in "$CERT_DIR/intermediate_ca.csr" \
  -CA "$CERT_DIR/root_ca.crt" -CAkey "$CERT_DIR/root_ca.key" \
  -CAcreateserial \
  -out "$CERT_DIR/intermediate_ca.crt" \
  -days $DAYS_VALID \
  -extfile <(printf "basicConstraints=CA:TRUE\nkeyUsage=keyCertSign,cRLSign")

# --- Server Certificate ---
echo "[3/5] Generating Server certificate..."
openssl req -newkey rsa:$RSA_BITS -nodes \
  -keyout "$CERT_DIR/server.key" \
  -out "$CERT_DIR/server.csr" \
  -subj "/C=$COUNTRY/ST=$STATE/O=$ORG/CN=mcp-server.example.com"

openssl x509 -req -in "$CERT_DIR/server.csr" \
  -CA "$CERT_DIR/intermediate_ca.crt" -CAkey "$CERT_DIR/intermediate_ca.key" \
  -CAcreateserial \
  -out "$CERT_DIR/server.crt" \
  -days $DAYS_VALID \
  -extfile <(printf "subjectAltName=DNS:mcp-server.example.com,DNS:localhost,IP:127.0.0.1\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth")

# --- Client Certificate ---
echo "[4/5] Generating Client certificate..."
openssl req -newkey rsa:$RSA_BITS -nodes \
  -keyout "$CERT_DIR/client.key" \
  -out "$CERT_DIR/client.csr" \
  -subj "/C=$COUNTRY/ST=$STATE/O=$ORG/OU=partner-name/CN=mcp-client.partner.com"

openssl x509 -req -in "$CERT_DIR/client.csr" \
  -CA "$CERT_DIR/intermediate_ca.crt" -CAkey "$CERT_DIR/intermediate_ca.key" \
  -CAcreateserial \
  -out "$CERT_DIR/client.crt" \
  -days $DAYS_VALID \
  -extfile <(printf "keyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=clientAuth")

# --- CA Bundle ---
echo "[5/5] Creating CA bundle..."
cat "$CERT_DIR/intermediate_ca.crt" "$CERT_DIR/root_ca.crt" > "$CERT_DIR/ca.crt"

echo ""
echo "============================================"
echo "Certificate generation complete."
echo ""
echo "Files:"
echo "  Root CA:          $CERT_DIR/root_ca.crt"
echo "  Intermediate CA:  $CERT_DIR/intermediate_ca.crt"
echo "  CA Bundle:        $CERT_DIR/ca.crt"
echo "  Server cert/key:  $CERT_DIR/server.crt, $CERT_DIR/server.key"
echo "  Client cert/key:  $CERT_DIR/client.crt, $CERT_DIR/client.key"
echo ""
echo "Update your .env:"
echo "  MTLS_CA_CERT=./certs/ca.crt"
echo "  MTLS_CLIENT_CERT=./certs/client.crt"
echo "  MTLS_CLIENT_KEY=./certs/client.key"
echo "  MTLS_SERVER_CERT=./certs/server.crt"
echo "  MTLS_SERVER_KEY=./certs/server.key"

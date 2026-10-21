# Converter Overview

The Hash examples in `hash.xml` need a host key. Keep 32 random bytes in a
secret environment variable as standard Base64, then pass only the variable
name through runtime configuration:

```bash
export DATAMIMIC_PSEUDONYMIZATION_KEY="$(openssl rand -base64 32)"
datamimic run datamimic.xml \
  --platform-configs '{"pseudonymization_key_env":"DATAMIMIC_PSEUDONYMIZATION_KEY"}'
```

Do not put the key value in the descriptor or project files.

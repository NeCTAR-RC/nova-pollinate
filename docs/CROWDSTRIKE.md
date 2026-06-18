# CrowdStrike Provider Documentation

## Overview

The CrowdStrike provider automatically generates vendor_data2 configuration for installing and configuring the CrowdStrike Falcon sensor on instances. Configuration is entirely managed through Vault secrets on a per-availability-zone basis.

## How It Works

1. **Nova requests vendor data** for a new instance during boot
2. **Pollinate receives the request** with the instance metadata. Nova does
   not include the availability zone in the vendordata context, so the
   provider looks the instance up via the Nova API and reads its
   `OS-EXT-AZ:availability_zone`
3. **CrowdStrike provider queries Vault** for AZ-specific configuration
4. **If configuration exists**, provider returns vendor_data2 with CrowdStrike settings
5. **Cloud-init receives vendor_data2** and runs the CrowdStrike module
6. **Module installs and configures** the Falcon sensor with the provided CID

## Vault Secrets Structure

All secrets are **per-availability-zone**. The Vault key uses the normalised
AZ name (uppercased, with hyphens preserved).

### Required Secrets Per AZ

For each availability zone where CrowdStrike should be deployed:

```
CROWDSTRIKE_<SITE>_CID                  - CrowdStrike Customer ID (required)
CROWDSTRIKE_<SITE>_INSTALLER_URL_DEB    - Debian/Ubuntu installer URL (required*)
CROWDSTRIKE_<SITE>_INSTALLER_URL_RPM    - RHEL/CentOS installer URL (required*)
CROWDSTRIKE_<SITE>_ENABLED              - Per-AZ opt-out (optional, default true)
CROWDSTRIKE_<SITE>_FAIL_IF_MISSING      - Fail-closed (optional, default false)
```

\* At least one installer URL (DEB or RPM) must be present.

Set `CROWDSTRIKE_<SITE>_ENABLED` to a false value (`false`, `0`, `no`, `off`)
to opt an AZ out without removing its secrets. The provider then skips the AZ
entirely, so no CID or installer URLs are injected.

### AZ Name Normalization

The provider normalizes AZ names to determine the Vault key. The full AZ name is preserved to allow granular per-AZ configuration:

| Availability Zone | Normalized Name | Vault Key Example |
|-------------------|-----------------|-------------------|
| `melbourne-qh2`   | `MELBOURNE-QH2`     | `CROWDSTRIKE_MELBOURNE-QH2_CID` |
| `melbourne-qh2-uom` | `MELBOURNE-QH2-UOM` | `CROWDSTRIKE_MELBOURNE-QH2-UOM_CID` |
| `monash-01`       | `MONASH-01`        | `CROWDSTRIKE_MONASH-01_CID` |
| `monash-02`       | `MONASH-02`        | `CROWDSTRIKE_MONASH-02_CID` |
| `tasmania`        | `TASMANIA`      | `CROWDSTRIKE_TASMANIA_CID` |
| `QRIScloud-02`    | `QRISCLOUD-02`     | `CROWDSTRIKE_QRISCLOUD-02_CID` |

The normalization process converts the AZ name to uppercase, preserving hyphens.

This preserves the full AZ identity, allowing different configurations for `melbourne-qh2` vs `melbourne-qh2-uom`, or `monash-01` vs `monash-02`.

### Example Vault Configuration

For Melbourne QH2 availability zone:
```
CROWDSTRIKE_MELBOURNE-QH2_CID = "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5-P6"
CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_DEB = "https://storage.example.com/crowdstrike/falcon-sensor_7.10.0-16303_amd64.deb"
CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_RPM = "https://storage.example.com/crowdstrike/falcon-sensor-7.10.0-16303.el8.x86_64.rpm"
```

For Melbourne QH2 UoM availability zone (different CID):
```
CROWDSTRIKE_MELBOURNE-QH2-UOM_CID = "X1Y2Z3A4B5C6D7E8F9G0H1I2J3K4L5-M6"
CROWDSTRIKE_MELBOURNE-QH2-UOM_INSTALLER_URL_DEB = "https://storage.example.com/crowdstrike/falcon-sensor_7.10.0-16303_amd64.deb"
CROWDSTRIKE_MELBOURNE-QH2-UOM_INSTALLER_URL_RPM = "https://storage.example.com/crowdstrike/falcon-sensor-7.10.0-16303.el8.x86_64.rpm"
```

For Monash 01 and Monash 02 availability zones (separate CIDs):
```
CROWDSTRIKE_MONASH-01_CID = "Z9Y8X7W6V5U4T3S2R1Q0P9O8N7M6L5-K4"
CROWDSTRIKE_MONASH-01_INSTALLER_URL_DEB = "https://storage.example.com/crowdstrike/falcon-sensor_7.10.0-16303_amd64.deb"
CROWDSTRIKE_MONASH-01_INSTALLER_URL_RPM = "https://storage.example.com/crowdstrike/falcon-sensor-7.10.0-16303.el8.x86_64.rpm"

CROWDSTRIKE_MONASH-02_CID = "P9O8N7M6L5K4J3I2H1G0F9E8D7C6B5-A4"
CROWDSTRIKE_MONASH-02_INSTALLER_URL_DEB = "https://storage.example.com/crowdstrike/falcon-sensor_7.10.0-16303_amd64.deb"
CROWDSTRIKE_MONASH-02_INSTALLER_URL_RPM = "https://storage.example.com/crowdstrike/falcon-sensor-7.10.0-16303.el8.x86_64.rpm"
```

## Behavior

### Per-AZ Opt-In

CrowdStrike installation is **opt-in per availability zone**:

- If secrets exist for an AZ → CrowdStrike installs
- If secrets do not exist → Installation skipped silently
- This allows gradual rollout across availability zones

### Error Handling

The provider is designed to fail gracefully:

| Scenario | Behavior |
|----------|----------|
| No CID found for AZ | Skip installation (INFO log) |
| AZ disabled (`ENABLED` false) | Skip installation (INFO log) |
| No installer URLs | Skip installation (ERROR log) |
| Instance has no availability zone | Skip installation (WARNING log) |
| Vault connection error | Provider fails, empty response |

The cloud-init module (`cc_crowdstrike`) also has fail-safe behavior:
- Installation errors are logged but don't halt boot (by default)
- `fail_if_missing: false` ensures instances still boot if CrowdStrike fails

## Enabling the Provider

### 1. Add Secrets to Vault

Add secrets for each AZ where CrowdStrike should deploy:

```bash
# Melbourne QH2
vault kv put k8s/nova-pollinate/secrets \
  CROWDSTRIKE_MELBOURNE-QH2_CID="YOUR-CID-HERE" \
  CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_DEB="https://..." \
  CROWDSTRIKE_MELBOURNE-QH2_INSTALLER_URL_RPM="https://..."

# Melbourne QH2 UoM (different CID)
vault kv put k8s/nova-pollinate/secrets \
  CROWDSTRIKE_MELBOURNE-QH2-UOM_CID="YOUR-CID-HERE" \
  CROWDSTRIKE_MELBOURNE-QH2-UOM_INSTALLER_URL_DEB="https://..." \
  CROWDSTRIKE_MELBOURNE-QH2-UOM_INSTALLER_URL_RPM="https://..."

# Monash 01
vault kv put k8s/nova-pollinate/secrets \
  CROWDSTRIKE_MONASH-01_CID="YOUR-CID-HERE" \
  CROWDSTRIKE_MONASH-01_INSTALLER_URL_DEB="https://..." \
  CROWDSTRIKE_MONASH-01_INSTALLER_URL_RPM="https://..."

# Monash 02
vault kv put k8s/nova-pollinate/secrets \
  CROWDSTRIKE_MONASH-02_CID="YOUR-CID-HERE" \
  CROWDSTRIKE_MONASH-02_INSTALLER_URL_DEB="https://..." \
  CROWDSTRIKE_MONASH-02_INSTALLER_URL_RPM="https://..."
```

### 2. Enable Provider in Configuration

Add `crowdstrike` to the providers list in `/etc/nova-pollinate/nova-pollinate.conf`:

```ini
[DEFAULT]
providers = nvidia_vgpu,windows_product_key,crowdstrike
```

Or via environment variable:

```bash
OS_DEFAULT__PROVIDERS=nvidia_vgpu,windows_product_key,crowdstrike
```

### 3. Restart Pollinate Service

```bash
systemctl restart nova-pollinate
```

### 4. Verify Configuration

Check the test endpoint to verify Vault connectivity:

```bash
curl http://localhost:5000/test
```

Expected response:
```json
{"OK": "Success"}
```

## Testing

### Unit Tests

Run the CrowdStrike provider tests:

```bash
tox -e py3 -- pollinate.tests.unit.providers.test_crowdstrike
```

### Integration Testing

1. **Mock instance launch** with test context. The availability zone is not
   read from this payload; the provider resolves it from the instance via the
   Nova API, so `instance-id` must reference a real instance in the target AZ:

```bash
curl -X POST http://localhost:5000/ \
  -H "Content-Type: application/json" \
  -H "X-Identity-Status: Confirmed" \
  -d '{
    "instance-id": "<real-instance-in-melbourne-qh2>",
    "project-id": "test-project"
  }'
```

2. **Expected response** (if Melbourne secrets configured). Pollinate keys the
   provider output under `crowdstrike` and Nova nests the whole response under
   the `nectar` dynamic target, so the guest sees it at
   `vendor_data2.nectar.crowdstrike`:

```json
{
  "crowdstrike": {
    "cid": "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5-P6",
    "installer_url": "https://storage.example.com/crowdstrike/falcon-sensor_7.10.0-16303_amd64.deb",
    "installer_url_deb": "https://storage.example.com/crowdstrike/falcon-sensor_7.10.0-16303_amd64.deb",
    "installer_url_rpm": "https://storage.example.com/crowdstrike/falcon-sensor-7.10.0-16303.el8.x86_64.rpm",
    "enabled": true,
    "fail_if_missing": false
  }
}
```

3. **Test AZ without configuration** (an instance in an AZ with no secrets):

Expected: Empty response `{}`

## Monitoring

### Logs

Provider logs to pollinate service logs:

```bash
journalctl -u nova-pollinate -f | grep crowdstrike
```

Key log messages:
- `Generated CrowdStrike config for instance <id> in AZ melbourne-qh2` - Successful config retrieval
- `No CrowdStrike CID found for AZ melbourne-qh2 (site: MELBOURNE-QH2), skipping installation` - AZ not configured
- `CrowdStrike disabled for AZ melbourne-qh2 (site: MELBOURNE-QH2), skipping` - AZ opted out
- `No CrowdStrike installer URLs found in Vault` - Missing installer URLs

### Cloud-Init Logs

On instances, check cloud-init logs:

```bash
# Cloud-init main log
grep -i crowdstrike /var/log/cloud-init.log

# Cloud-init output
grep -i crowdstrike /var/log/cloud-init-output.log
```

### Verification

Check if Falcon sensor is installed and running:

```bash
# Service status
systemctl status falcon-sensor

# Falconctl status
sudo /opt/CrowdStrike/falconctl -g --cid
```

## Updating Configuration

### Updating CID or Installer URLs

1. Update Vault secrets:

```bash
vault kv patch k8s/nova-pollinate/secrets \
  CROWDSTRIKE_MELBOURNE_CID="NEW-CID-HERE"
```

2. Changes take effect immediately (60-second cache)
3. Only new instances get updated config
4. Existing instances are not affected

### Adding New Availability Zone

1. Add secrets for new AZ (e.g., `tasmania`):

```bash
vault kv put k8s/nova-pollinate/secrets \
  CROWDSTRIKE_TASMANIA_CID="CID-HERE" \
  CROWDSTRIKE_TASMANIA_INSTALLER_URL_DEB="https://..." \
  CROWDSTRIKE_TASMANIA_INSTALLER_URL_RPM="https://..."
```

2. No code changes or restarts needed
3. New instances in that AZ will automatically receive configuration

### Removing Availability Zone

1. Delete secrets from Vault (e.g., removing `tasmania`):

```bash
vault kv patch k8s/nova-pollinate/secrets \
  CROWDSTRIKE_TASMANIA_CID="" \
  CROWDSTRIKE_TASMANIA_INSTALLER_URL_DEB="" \
  CROWDSTRIKE_TASMANIA_INSTALLER_URL_RPM=""
```

2. New instances will skip installation
3. Existing instances remain unaffected

## Security Considerations

### Secrets Management

- **CIDs are sensitive**: Treat as secrets, store only in Vault
- **Installer URLs**: Should use HTTPS
- **Access control**: Limit Vault access to pollinate service account
- **Rotation**: Update CIDs by changing Vault secrets (no code changes)

### User Override Protection

- Users **cannot** override vendor_data2 configuration
- CrowdStrike config comes from immutable vendor_data (operator-controlled)
- User-data cannot disable or modify CrowdStrike installation

### Network Security

- Installer downloads use HTTPS with retries
- Downloads occur during cloud-init (early boot)
- Ensure instances have network access to installer URLs

## Troubleshooting

### Provider Not Running

**Symptom**: No CrowdStrike output in pollinate response

**Check**:
1. Provider enabled in config: `grep providers /etc/nova-pollinate/nova-pollinate.conf`
2. Provider loaded: `journalctl -u nova-pollinate | grep "Loaded providers"`

### Vault Connection Issues

**Symptom**: 500 error from pollinate, or "Error: Failed to get secrets"

**Check**:
1. Vault connectivity: `curl http://localhost:5000/test`
2. Vault authentication: Check pollinate logs for auth errors
3. Kubernetes token valid (in production deployments)

### Secrets Not Found

**Symptom**: Empty response, log shows "No CrowdStrike CID found"

**Check**:
1. AZ normalization: `melbourne-qh2` → `MELBOURNE-QH2`, `monash-01` → `MONASH-01`
2. Vault key names: `CROWDSTRIKE_<AZ>_CID` (e.g., `CROWDSTRIKE_MELBOURNE-QH2_CID`)
3. Vault secrets exist: `vault kv get k8s/nova-pollinate/secrets`

### Installation Failing on Instances

**Symptom**: Instances boot but Falcon sensor not installed

**Check**:
1. Cloud-init logs: `/var/log/cloud-init.log`
2. Vendor data received: `cloud-init query vendordata`
3. Network access to installer URLs
4. Installer package compatibility with OS

## Architecture

### Data Flow

```
Nova Instance Launch
       ↓
Nova requests vendor data (POST /pollinate)
       ↓
Pollinate receives request
       ↓
CrowdStrike provider.run(context)
       ↓
Provider resolves AZ via Nova API (OS-EXT-AZ:availability_zone)
       ↓
Provider queries Vault for CROWDSTRIKE_<AZ>_*
       ↓
       ├─ Secrets found → Return CrowdStrike config
       └─ Secrets not found → Return {} (skip)
       ↓
Pollinate merges provider outputs
       ↓
Nova receives vendor_data2 response
       ↓
Cloud-init fetches vendor_data2
       ↓
cc_crowdstrike module runs (cloud_final_modules)
       ↓
       ├─ Download installer from URL
       ├─ Install package (dpkg/rpm)
       ├─ Configure with CID (falconctl)
       └─ Start falcon-sensor service
       ↓
Instance fully booted with Falcon sensor
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Vault** | Store CIDs and installer URLs per AZ |
| **Pollinate Provider** | Query Vault, generate vendor_data2 |
| **Nova** | Request and inject vendor_data2 |
| **Cloud-init Module** | Install and configure Falcon sensor |
| **Falcon Sensor** | EDR monitoring and protection |

## References

- [Cloud-init vendor_data documentation](https://cloudinit.readthedocs.io/en/latest/topics/vendordata.html)
- [CrowdStrike Falcon sensor documentation](https://falcon.crowdstrike.com/documentation/)
- [Nova pollinate provider development](../README.md)

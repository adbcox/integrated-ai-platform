# Zabbix Initial Setup - EXECUTE MANUALLY

## 1. Access Web UI
URL: http://192.168.10.145:10080
Login: Admin / zabbix

## 2. CHANGE ADMIN PASSWORD (Critical!)
1. Click "User settings" (top right)
2. Click "Change password"
3. New password: [Use password manager - min 16 chars]
4. Click "Update"

## 3. Configure Housekeeping (Enable TimescaleDB-aware deletion)
1. Navigate to: Administration → General → Housekeeping
2. Enable "Override item history period": ✅
3. Enable "Override item trend period": ✅
4. Storage period: History = 30 days, Trends = 365 days
5. Click "Update"

## 4. Create Read-Only User for Grafana
1. Administration → Users → Create user
   - Alias: grafana_reader
   - Name: Grafana
   - Surname: Integration
   - Groups: Add "Guests" (read-only)
   - Password: [Generate secure password]
   - Frontend access: Disabled
   - Auto-login: No
2. Click "Add"

## 5. Disable Guest Access
1. Administration → Authentication
2. "Enable access for guest users": Uncheck
3. Click "Update"

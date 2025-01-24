@secure()
param secretsObject object
param kvResourceName string
resource keyVaultSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01'  = [for secret in secretsObject.secrets: {
name: '${kvResourceName}/${secret.secretName}'
properties: {
 value: secret.secretValue
 }
}]

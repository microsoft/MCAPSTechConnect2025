// Main.bicep
param location string = resourceGroup().location
//param location string = 'westus'
param prefix string 
var functionAppName = '${prefix}funcapp'
var openAIName = '${prefix}_aoai2'
var redisName = '${prefix}redis'
var appInsightsName = '${prefix}appinsg'
var keyVaultName = '${prefix}kv2'
var storageAccName = '${prefix}stgacc' 

// Define the App Service Plan for the Function App
resource functionAppPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${functionAppName}-plan'
  location: location
  sku: {
    tier: 'Dynamic'
    name: 'EP1'
  }
  properties: {
    reserved: true
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enableSoftDelete: true
  }
}

var functionAppNames = [
    '${functionAppName}1'
    '${functionAppName}2'
    '${functionAppName}3'
    '${functionAppName}4'
  ]

// Four function app created
resource functionApps 'Microsoft.Web/sites@2022-03-01' = [for i in range(0, 4): {
  name: functionAppNames[i]
  location: location
  kind: 'functionapp'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: functionAppPlan.id
    httpsOnly: true
  }
  dependsOn: [
    keyVault
  ]
}]

 // RBAC Role Assignment for Function App to access Key Vault
 resource keyVaultAccessRoleAssignments 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = [for i in range(0, 4): {
   name: guid(keyVault.id, 'KeyVaultAccess', functionApps[i].id)
   scope: keyVault
   properties: {
     roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7') // Key Vault Secrets User role
     principalId: functionApps[i].identity.principalId
    principalType: 'ServicePrincipal'
  }
 }]

// Azure OpenAI Service
resource openAI 'Microsoft.CognitiveServices/accounts@2022-12-01' = {
   name: openAIName
   location: location
   sku: {
     name: 'S0'
   }
   kind: 'OpenAI'
   properties: {
     apiProperties: {}
   }
 }

// Redis Cache
resource redisCache 'Microsoft.Cache/Redis@2024-11-01' = {
  name: redisName
  location: location
  properties: {
    sku: {
      name: 'basic'
      family: 'C'
      capacity: 1
    }
    enableNonSslPort: true
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  properties: {
    Application_Type: 'web'
  }
}

// Storage Account
resource storageaccount 'Microsoft.Storage/storageAccounts@2021-04-01' = {
  name: storageAccName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
  }
}


// Secret object
var secretsObject = {
   secrets: [
    {
      secretName:  'GPT-DEPLOYMENT-NAME'
      secretValue: 'gpt-4o'
    }
     {
       secretName:  'OPENAI_API_KEY'
       secretValue: '1'
     }
     {
       secretName:  'OPENAI_API_BASE'
       secretValue: 'https://${openAIName}.openai.azure.com/'
     }
     {
       secretName:  'OPENAI_API_VERSION'
       secretValue: '2024-04-01-perview'
     }
     
     {
       secretName:  'REDIS_HOST'
       secretValue: '${redisName}.redis.cache.windows.net'
     }
     {
       secretName:  'REDIS_PASSWORD'
       secretValue:  '1'
     }
   ]
 }

module kvSaSecretsModuleResource './keyVaultSecrets.bicep' = {
  name: 'kvSaSecertsDeploy'
  params: {
    secretsObject: secretsObject
    kvResourceName: keyVaultName
  }
 dependsOn: [
  keyVault
  ]
}

output functionAppId string = functionApps[1].id
output openAIId string = openAI.id
output redisId string = redisCache.id
output appInsightsId string = appInsights.id
output keyVaultId string = keyVault.id

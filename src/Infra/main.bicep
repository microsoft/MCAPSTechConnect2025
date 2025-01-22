// Main.bicep
param location string = resourceGroup().location
param msaid string
//param location string = 'westus'
param prefixparam string
var year = '2025'
var month = '01'
var day = '22'
var prefix = '${prefixparam}${year}${month}${day}'

var functionAppName = '${prefix}funcapp'
var openAIName = '${prefix}_aoai2'
var redisName = '${prefix}redis'
var appInsightsName = '${prefix}appinsg'
var keyVaultName = '${prefix}kv2'
var storageAccName = '${prefix}stgacc'
var searchServicename = '${prefix}search'
var webappname = '${prefix}webapp'
var botserviceName = '${prefix}botsvc'

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

// Define the App Service Plan for the Web App
resource webAppPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${webappname}-plan'
  location: location
  sku: {
    tier: 'Standard'
    name: 'S1'
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
// resource keyVaultAccessRoleAssignments 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = [for i in range(0, 4): {
 //  name: guid(keyVault.id, 'KeyVaultAccess', functionApps[i].id)
  // scope: keyVault
  // properties: {
  //   roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7') // Key Vault Secrets User role
  //   principalId: functionApps[i].identity.principalId
   //  principalType: 'ServicePrincipal'
   //}
 //}]

// Web App
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webappname
  location: location
  kind: 'app'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: webAppPlan.id
    httpsOnly: true
  }
  dependsOn: [
    keyVault
  ]
}

// RBAC Role Assignment for Web App to access Key Vault
 resource webAppKeyVaultAccessRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
   name: guid(keyVault.id, 'KeyVaultAccess', webApp.id)
   scope: keyVault
   properties: {
     roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7') // Key Vault Secrets User role
     principalId: webApp.identity.principalId
     principalType: 'ServicePrincipal'
   }
 }

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
      name: 'free'
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

// AI Search Service
  resource searchService 'Microsoft.Search/searchServices@2020-08-01' = {
    name: searchServicename
    location: location
    sku: {
      name: 'standard'
    }
    properties: {
      replicaCount: 1
      partitionCount: 1
      publicNetworkAccess: 'Enabled'
    }
  }

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-04-01' = {
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

// Define the App Service Plan for the Bot Service
resource botServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${botserviceName}-plan'
  location: location
  sku: {
    tier: 'Standard'
    name: 'S1'
  }
  properties: {
    reserved: true
  }
}

// Azure Bot Service
resource botService 'Microsoft.BotService/botServices@2023-09-15-preview' = {
  name: botserviceName
  location: 'global'
  sku: {
    name: 'F0'
  }
  kind: 'azurebot'
  properties: {
    displayName: botserviceName
    endpoint: 'https://${botserviceName}.azurewebsites.net/api/messages'
    msaAppId: msaid // Replace with your Microsoft App ID
    developerAppInsightKey: appInsights.properties.InstrumentationKey // Replace with your Application Insights Key
    isCmekEnabled: false
    isStreamingSupported: false
  }
  dependsOn: [
    botServicePlan
  ]
}

// Secret object
//var secretsObject = {
//   secrets: [
//     {
//       secretName:  'OPENAI_API_KEY'
//       secretValue: '1'
//     }
//     {
//       secretName:  'OPENAI_API_BASE'
//       secretValue: 'https://${openAIName}.openai.azure.com/'
//     }
//     {
//       secretName:  'OPENAI_API_VERSION'
//       secretValue: 'gpt4o'
//     }
//     {
//       secretName:  'GPT_DEPLOYMENT_NAME'
//       secretValue: 'gpt-4o'
//     }
//     {
//       secretName:  'MODULE_NAME'
//       secretValue:  'Query-Orchestrator'
//     }
//     {
//       secretName:  'USE_CACHE'
//       secretValue:  false
//     }
//     {
//       secretName:  'CACHE_TYPE'
//       secretValue:  'redis'
//     }
//     {
//       secretName:  'REDIS_HOST'
//       secretValue: '1'
//     }
//     {
//       secretName:  'REDIS_PASSWORD'
//       secretValue:  '1'
//     }
//     {
//       secretName:  'HR_INSIGHT_SERVICE_URL'
//       secretValue:  'https://${functionAppNames[2]}.azurewebsites.net/'
//     }
//     {
//       secretName:   'WORKDAY_SERVICE_URL'
//       secretValue:  'https://${functionAppNames[3]}.azurewebsites.net/'
//     }
//   ]
// }

//module kvSaSecretsModuleResource './keyVaultSecrets.bicep' = {
 // name: 'kvSaSecertsDeploy'
  //params: {
  ///  secretsObject: secretsObject
   // kvResourceName: keyVaultName
 // }
  //dependsOn: [
   // keyVault
  //]
//}


output functionAppId string = functionApps[1].id
output openAIId string = openAI.id
output redisId string = redisCache.id
output appInsightsId string = appInsights.id
output keyVaultId string = keyVault.id

---
name: aws-cdk-ts
description: AWS CDK v2 with TypeScript reference guide for defining and deploying cloud infrastructure. Use this skill whenever the user is working with AWS CDK, importing from aws-cdk-lib, writing infrastructure as code for AWS, creating CloudFormation stacks via CDK, or asks about CDK commands (cdk init, synth, diff, deploy, bootstrap, destroy). Also trigger when you see CDK constructs like Stack, Construct, or aws-cdk-lib imports in the codebase, when the user mentions deploying to ECS/ECR/ALB/S3/RDS/Lambda via CDK, or when they ask how to define AWS resources in TypeScript. Even if the user just says "deploy to AWS" or "set up infrastructure", consider triggering this skill if CDK is the appropriate tool.
---

# AWS CDK v2 with TypeScript

Reference guide for defining AWS infrastructure as code using CDK v2 and TypeScript.

**CDK in one sentence:** You write TypeScript classes that describe AWS resources, CDK converts them to CloudFormation templates, and CloudFormation deploys them.

## CLI Commands

### Project setup
```bash
mkdir my-app && cd my-app
npx cdk init app --language typescript
# Generates package.json with aws-cdk-lib + constructs already installed
# Directory name is used for code generation (stack names, file names)
```

### Bootstrap (one-time per account/region)
```bash
cdk bootstrap aws://ACCOUNT_ID/REGION
cdk bootstrap --profile my-profile aws://123456789/us-east-1
```
Creates a `CDKToolkit` CloudFormation stack with an S3 bucket for assets and IAM roles for deployment. Only creates new resources.

**Security note:** The `CloudFormationExecutionRole` created by bootstrap has `AdministratorAccess` by default. For production, customize with `--cloudformation-execution-policies` to restrict what CDK can create. Use permission boundaries rather than fine-grained restrictions — incomplete permissions can leave stacks in unrecoverable states during rollback.

### Core workflow
```bash
cdk synth              # Generate CloudFormation template (to cdk.out/)
cdk diff               # Show what will change vs deployed state
cdk deploy             # Deploy the stack (auto-builds TypeScript first)
cdk deploy StackName   # Deploy a specific stack
cdk destroy            # Tear down the stack
cdk list               # List all stacks in the app
```
Note: `synth` and `deploy` auto-compile TypeScript — no need to run `npm run build` first (though it can catch errors earlier).

### Key flags
| Flag | Purpose |
|------|---------|
| `--require-approval broadening` | Prompt only for security-widening changes |
| `--require-approval never` | Skip approval (CI/CD only) |
| `--hotswap` | Fast-update Lambda/ECS/StepFunctions without full CloudFormation deploy |
| `--no-rollback` | Don't roll back on failure (faster debugging) |
| `--outputs-file out.json` | Write stack outputs to JSON |
| `--profile NAME` | Use specific AWS profile |
| `--context key=value` | Pass runtime context |
| `--app "command"` | Override app command |

### Stack selection patterns
```bash
cdk deploy StackA StackB    # Named stacks
cdk deploy "*"              # All stacks
cdk deploy "Pipeline/**"    # Nested stacks by path
```

## Project Structure

```
my-app/
  bin/my-app.ts          # Entry point — instantiate stacks
  lib/
    my-stack.ts          # Stack definitions (constructs + resources)
  cdk.json               # CDK config (app command, context, feature flags)
  tsconfig.json
  package.json           # aws-cdk-lib + constructs already included
```

### Entry point pattern (`bin/my-app.ts`)
```typescript
import * as cdk from 'aws-cdk-lib'
import { MyStack } from '../lib/my-stack'

const app = new cdk.App()
const env = { account: '123456789012', region: 'us-east-1' }

new MyStack(app, 'MyStack-Stage', { env, stageName: 'stage' })
new MyStack(app, 'MyStack-Prod', { env, stageName: 'prod' })
```

### Stack pattern (`lib/my-stack.ts`)
```typescript
import * as cdk from 'aws-cdk-lib'
import { Construct } from 'constructs'

// Always define typed props — avoid `any`. Extend StackProps/ConstructProps.
// Mark values that shouldn't change after creation as readonly.
interface MyStackProps extends cdk.StackProps {
  readonly stageName: string
  readonly desiredCount: number
}

export class MyStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: MyStackProps) {
    super(scope, id, props)
    // Define resources here using props, not process.env
  }
}
```

## Key Concepts

### Constructs (L1, L2, L3)
- **L1 (Cfn*):** Direct CloudFormation mapping. Prefix `Cfn`. You set every property.
- **L2:** Opinionated defaults + helper methods (`.grantRead()`, `.addToPolicy()`). Most of what you use.
- **L3 (Patterns):** Multi-resource abstractions (e.g., `ApplicationLoadBalancedFargateService`).

### Model with Constructs, deploy with Stacks
Constructs are logical units (a "Website", an "API"). Stacks are deployment units. Don't use a Stack where a Construct would do — compose Constructs together, then wrap in a Stack for deployment.
```typescript
// Construct = reusable logical unit
class ApiService extends Construct {
  constructor(scope: Construct, id: string, props: ApiServiceProps) {
    super(scope, id)
    // task def, service, target group, etc.
  }
}

// Stack = deployment unit that composes constructs
class AppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: AppStackProps) {
    super(scope, id, props)
    new ApiService(this, 'Api', { /* props */ })
  }
}
```

### Environments (account + region)
Every stack deploys to an environment (account + region). Specify via the `env` prop:
```typescript
// Hard-coded (recommended for production — deterministic)
new MyStack(app, 'Prod', { env: { account: '123456789012', region: 'us-east-1' } })

// From CLI profile (useful for dev — resolves from ~/.aws/config)
new MyStack(app, 'Dev', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }
})
```
**Critical:** `fromLookup` methods (VPC, ALB, hosted zones, etc.) only work when `env` is explicitly set. Environment-agnostic stacks (no `env`) cannot look up existing resources. Use `--profile` to select which AWS credentials to use: `cdk deploy --profile my-profile`.

### Configure via props, not environment variables
Using `process.env` inside constructs/stacks is an anti-pattern — it creates machine dependencies and makes synthesis non-deterministic. Pass all configuration through typed props objects. Environment variables are acceptable only at the top-level app entry point (`bin/`) for selecting which stacks to deploy.

### Make decisions at synthesis time
Prefer TypeScript conditionals over CloudFormation `Conditions`/`Fn::If`. Your programming language is more powerful than CloudFormation's expression language.
```typescript
// Do this — full language power
if (props.stageName === 'prod') {
  new MonitoringConstruct(this, 'Monitoring')
}
// Not CloudFormation Conditions
```

### Logical ID stability (critical for stateful resources)
CDK derives each resource's CloudFormation logical ID from its construct `id` + position in the construct tree. If a logical ID changes, CloudFormation **replaces** the resource — meaning data loss for databases, S3 buckets, etc. Be careful when renaming constructs, moving them to different parents, or changing instantiation order. Don't nest stateful resources inside constructs that are likely to be reorganized.

### Referencing existing resources (read-only, no ownership)
```typescript
// CDK will NOT manage or modify these — just wire new resources to them
const vpc = ec2.Vpc.fromLookup(this, 'Vpc', { vpcId: 'vpc-123' })
const cluster = ecs.Cluster.fromClusterAttributes(this, 'Cluster', {
  clusterName: 'my-cluster', vpc, securityGroups: []
})
const listener = elbv2.ApplicationListener.fromLookup(this, 'Listener', {
  listenerArn: 'arn:aws:elasticloadbalancing:...'
})
const sg = ec2.SecurityGroup.fromSecurityGroupId(this, 'Sg', 'sg-123')
```

### Cross-stack references
```typescript
// Stack A exports
this.bucket = new s3.Bucket(this, 'Bucket')

// Stack B imports (pass via props)
new lambda.Function(this, 'Fn', { environment: { BUCKET: props.bucket.bucketName } })
```

### Exposing stack outputs
```typescript
// CfnOutput prints values after deploy and exports to CloudFormation
new cdk.CfnOutput(this, 'ServiceUrl', { value: functionUrl.url })
new cdk.CfnOutput(this, 'RepoUri', { value: repo.repositoryUri })
```
Use `--outputs-file out.json` with `cdk deploy` to capture these as JSON.

## Common Constructs (TypeScript)

All imports from `aws-cdk-lib` submodules:
```typescript
import * as ec2 from 'aws-cdk-lib/aws-ec2'
import * as ecs from 'aws-cdk-lib/aws-ecs'
import * as ecr from 'aws-cdk-lib/aws-ecr'
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2'
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager'
import * as ssm from 'aws-cdk-lib/aws-ssm'
import * as route53 from 'aws-cdk-lib/aws-route53'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as logs from 'aws-cdk-lib/aws-logs'
```

### ECR Repository
```typescript
const repo = new ecr.Repository(this, 'Repo', {
  repositoryName: 'my-app',
  removalPolicy: cdk.RemovalPolicy.RETAIN,  // Keep images if stack deleted
  lifecycleRules: [{ maxImageCount: 20 }],
})
```

### ECS Task Definition (EC2)
```typescript
const taskDef = new ecs.Ec2TaskDefinition(this, 'TaskDef', {
  networkMode: ecs.NetworkMode.AWS_VPC,
})

taskDef.addContainer('app', {
  image: ecs.ContainerImage.fromEcrRepository(repo, 'latest'),
  memoryLimitMiB: 1024,
  cpu: 512,
  portMappings: [{ containerPort: 3000 }],
  logging: ecs.LogDrivers.awsLogs({
    logGroup: new logs.LogGroup(this, 'Logs', {
      logGroupName: '/ecs/my-app',
      retention: logs.RetentionDays.TWO_WEEKS,
    }),
    streamPrefix: 'app',
  }),
  environment: { KEY: 'value' },                    // Non-sensitive (visible in CloudFormation)
  secrets: {                                         // Sensitive (resolved at container start)
    DB_PASS: ecs.Secret.fromSecretsManager(secret, 'dbPassword'),
    API_KEY: ecs.Secret.fromSsmParameter(param),
  },
})
```

### ECS Task Definition (Fargate)
```typescript
const taskDef = new ecs.FargateTaskDefinition(this, 'TaskDef', {
  cpu: 512,
  memoryLimitMiB: 1024,
})
// addContainer same as above
```

### ECS Service
```typescript
const service = new ecs.Ec2Service(this, 'Service', {
  cluster,
  taskDefinition: taskDef,
  desiredCount: 1,
  circuitBreaker: { rollback: true },  // Auto-rollback on failure
  minHealthyPercent: 100,
  maxHealthyPercent: 200,
})
// For Fargate: use ecs.FargateService with same pattern
```

### ALB Target Group + Listener Rule
```typescript
const tg = new elbv2.ApplicationTargetGroup(this, 'TG', {
  vpc,
  port: 3000,
  protocol: elbv2.ApplicationProtocol.HTTP,
  targetType: elbv2.TargetType.IP,
  healthCheck: {
    path: '/api/health',
    interval: cdk.Duration.seconds(30),
    healthyThresholdCount: 2,
    unhealthyThresholdCount: 3,
  },
})
service.attachToApplicationTargetGroup(tg)

new elbv2.ApplicationListenerRule(this, 'Rule', {
  listener,
  priority: 10,
  conditions: [elbv2.ListenerCondition.hostHeaders(['my-app.example.com'])],
  targetGroups: [tg],
})
```

### Security Groups
```typescript
const sg = new ec2.SecurityGroup(this, 'SG', {
  vpc,
  description: 'My service',
  allowAllOutbound: true,
})
sg.addIngressRule(ec2.Peer.securityGroup(albSg), ec2.Port.tcp(3000), 'ALB access')
```

### Secrets Manager
```typescript
// Reference existing secret (don't create secrets with values in CDK!)
const secret = secretsmanager.Secret.fromSecretNameV2(this, 'Secret', 'my-app/stage/secrets')

// Access JSON field in ECS
ecs.Secret.fromSecretsManager(secret, 'dbPassword')
```

### SSM Parameter Store
```typescript
// Read at deploy time
const value = ssm.StringParameter.valueForStringParameter(this, '/my-app/stage/db-host')

// Reference for ECS secrets
const param = ssm.StringParameter.fromStringParameterName(this, 'Param', '/my-app/key')
ecs.Secret.fromSsmParameter(param)
```

### Route 53
```typescript
const zone = route53.HostedZone.fromLookup(this, 'Zone', { domainName: 'example.com' })
new route53.ARecord(this, 'Alias', {
  zone,
  recordName: 'my-app',
  target: route53.RecordTarget.fromAlias(
    new route53_targets.LoadBalancerTarget(alb)
  ),
})
```

### IAM — prefer grants over manual policies
```typescript
bucket.grantRead(lambdaFunction)       // CDK creates minimal IAM policy
table.grantReadWriteData(service.taskDefinition.taskRole)
secret.grantRead(service.taskDefinition.executionRole)
```
Don't prevent CDK from creating IAM roles — it creates least-privilege policies automatically via grants. Use permission boundaries or SCPs to limit what those roles can do, rather than blocking role creation entirely (which forces workarounds that are less secure).

### CI/CD IAM policy for assuming CDK roles
For CI/CD pipelines (Bitbucket Pipelines, GitHub Actions, etc.) to deploy via CDK, the pipeline's IAM role needs permission to assume the CDK bootstrap roles:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sts:AssumeRole",
    "Resource": "*",
    "Condition": {
      "StringEquals": {
        "iam:ResourceTag/aws-cdk:bootstrap-role": [
          "image-publishing", "file-publishing", "deploy", "lookup"
        ]
      }
    }
  }]
}
```

### CloudWatch Logs
```typescript
new logs.LogGroup(this, 'Logs', {
  logGroupName: '/ecs/my-app',
  retention: logs.RetentionDays.TWO_WEEKS,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
})
```

## Safety Best Practices

### Always diff before deploy
```bash
cdk diff    # Review every line before deploying
```

### Protect stateful resources
```typescript
// RETAIN = if CDK stack is deleted, the resource survives
new ecr.Repository(this, 'Repo', { removalPolicy: cdk.RemovalPolicy.RETAIN })
new rds.DatabaseInstance(this, 'DB', { removalPolicy: cdk.RemovalPolicy.RETAIN })
```

### Circuit breaker for ECS
```typescript
new ecs.FargateService(this, 'Svc', {
  circuitBreaker: { rollback: true },  // Auto-rollback if containers fail
})
```

### Don't put secrets in CDK code
Secrets end up in CloudFormation templates and git history. Create them manually via CLI/console, then reference by name/ARN in CDK.

### Commit cdk.context.json
CDK caches lookup results (VPC IDs, AZs, etc.) in `cdk.context.json`. Commit this file — it ensures deterministic builds. Refresh intentionally with `cdk context --reset`.

### Let CDK generate resource names
Don't hardcode names — it prevents deploying the same stack twice and makes replacement impossible. Reference generated names via construct attributes (`bucket.bucketName`, `table.tableName`) and pass them to runtime code via environment variables or SSM.

### Separate stateful from stateless stacks
Put databases, S3 buckets, and VPCs in their own stack with termination protection. Stateless resources (services, functions) can be freely destroyed and recreated. Don't nest stateful resources inside constructs that might be renamed or reorganized — renaming changes the logical ID and triggers replacement.

### Model all environments in code
Create a separate stack instance per environment with configuration baked into source code. This makes builds deterministic — a given commit always produces the same templates.
```typescript
new AppStack(app, 'App-Stage', { env, stageName: 'stage', desiredCount: 1 })
new AppStack(app, 'App-Prod', { env, stageName: 'prod', desiredCount: 3 })
```

### Use grants for IAM, not manual policies
`bucket.grantRead(lambda)` creates minimally-scoped IAM policies automatically. If you need org-level guardrails, use SCPs and permission boundaries rather than restricting CDK's grant system.

### Set explicit removal policies and log retention
CDK defaults retain everything forever. Set explicit `removalPolicy` and `retention` on every resource to avoid unexpected storage costs. Use Aspects to validate these across all stacks.

## Docs Reference

- Getting started: https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html
- TypeScript guide: https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-typescript.html
- CLI reference: https://docs.aws.amazon.com/cdk/v2/guide/cli.html
- Best practices: https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html
- API reference: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-construct-library.html
- Construct Hub: https://constructs.dev/

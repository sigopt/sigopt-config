// https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-identity-documents.html
// http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
export const AWS_METADATA_URL = "http://169.254.169.254/latest";
export const INSTANCE_IDENTITY_DOC_URL =
  `${AWS_METADATA_URL}/dynamic/instance-identity/document`;
export const NOT_AVAILABLE = Symbol("NOT_AVAILABLE");

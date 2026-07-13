data "aws_iam_policy_document" "db_backup_assume_role" {
  statement {
    actions = [
      "sts:AssumeRole",
      "sts:TagSession",
    ]

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "db_backup" {
  statement {
    sid = "ListBackupPrefix"
    actions = [
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
    ]
    resources = [
      "arn:aws:s3:::${var.db_backup_s3_bucket_name}",
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "${var.db_backup_s3_prefix}/*",
      ]
    }
  }

  statement {
    sid = "ReadWriteBackupObjects"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetObject",
      "s3:ListMultipartUploadParts",
      "s3:PutObject",
    ]
    resources = [
      "arn:aws:s3:::${var.db_backup_s3_bucket_name}/${var.db_backup_s3_prefix}/*",
    ]
  }
}

resource "aws_iam_role" "db_backup" {
  name               = "${local.name_prefix}-db-backup"
  assume_role_policy = data.aws_iam_policy_document.db_backup_assume_role.json
}

resource "aws_iam_role_policy" "db_backup" {
  name   = "${local.name_prefix}-db-backup"
  role   = aws_iam_role.db_backup.id
  policy = data.aws_iam_policy_document.db_backup.json
}

resource "aws_eks_pod_identity_association" "db_backup" {
  for_each = toset([
    "recipe-rescue-staging",
    "recipe-rescue-production",
    "recipe-rescue-production-data",
  ])

  cluster_name    = module.eks.cluster_name
  namespace       = each.value
  service_account = "recipe-rescue-db-backup"
  role_arn        = aws_iam_role.db_backup.arn
}

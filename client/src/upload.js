import S3FFClient from 'django-s3-file-field';
import UploadBase from '@girder/components/src/utils/UploadBase';

class BatchCSVUploadHandler extends UploadBase {
  async start() {
    const fd = new FormData();
    fd.append('csvfile', this.file);
    fd.append('dataset', this.parent.datasetId);

    this.progress({ indeterminate: true });

    return (await this.$rest.post('upload_batches', fd, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })).data;
  }
}

class FileUploadHandler extends UploadBase {
  constructor(file, opts) {
    super(file, opts);
    this.s3FFClient = new S3FFClient(opts.$rest.defaults.baseURL + 's3-upload');
  }

  async start() {
    const resp = await this.$rest.get('pending_uploads', {
      params: {
        batch: this.parent.batchId,
        name: this.file.name,
      },
    });
    if (resp.data.results.length === 0) {
      throw {
        response: {
          data: {
            message: `There is no pending upload with the name "${this.file.name}".`
          },
        },
      };
    }

    const pendingUpload = resp.data.results[0].id;
    // TODO progress
    const data = await this.s3FFClient.uploadFile(this.file, this.parent.fieldId);

    return (await this.$rest.post('images', {
      pending_upload: pendingUpload,
      blob: data.value,
    })).data;
  }
}

export {
  BatchCSVUploadHandler,
  FileUploadHandler,
};

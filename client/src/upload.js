import UploadBase from '@girder/components/src/utils/UploadBase';

class CSVUploadHandler extends UploadBase {
  async start() {
    const fd = new FormData();
    fd.append('csvfile', this.file);
    fd.append('dataset', this.parent.datasetId);
    this.progress({ indeterminate: true });
    const result = (await this.$rest.post('upload_batches', fd, {
      onUploadProgress: (e) => this.progress({
        indeterminate: !e.lengthComputable,
        current: e.loaded,
        size: e.total,
      }),
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })).data;

    this.progress({
      indeterminate: false,
      size: this.file.size,
      current: this.file.size,
    });

    return result;
  }

  async resume() {
    return this.start();
  }
}

export {
  CSVUploadHandler,
};

<template>
  <div>
    <girder-upload
      :dest="{ datasetId }"
      :multiple="false"
      accept="text/csv"
      :upload-cls="BatchCSVUploadHandler"
      @done="uploadDone"
    >
      <template #header>
        <v-card-title primary-title>
          <div>
            <div class="title">
              Upload a CSV listing images to be uploaded
            </div>
          </div>
        </v-card-title>
      </template>
    </girder-upload>
  </div>
</template>

<script>
import GirderUpload from '@girder/components/src/components/Upload.vue';
import { BatchCSVUploadHandler } from '../upload';

export default {
  components: {
    GirderUpload,
  },
  props: {
    datasetId: {
      required: true,
      type: String,
    },
  },
  created() {
    this.BatchCSVUploadHandler = BatchCSVUploadHandler;
  },
  methods: {
    uploadDone([result]) {
      this.$router.push(`/upload/${result.id}`);
    },
  },
};
</script>

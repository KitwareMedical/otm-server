<template>
  <div>
    <girder-upload
      :dest="{ datasetId }"
      :multiple="false"
      accept="text/csv"
      :upload-cls="UploadHandler"
    >
      <template #header>
        <v-card-title primary-title>
          <div>
            <div class="headline">
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
import { CSVUploadHandler } from '../upload';

export default {
  components: {
    GirderUpload,
  },
  props: {
    datasetId: {
      required: true,
      type: Number,
    },
  },
  data() {
    return {
      UploadHandler,
    };
  },
};
</script>

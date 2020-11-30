import Vue from 'vue';
import Vuetify from 'vuetify';
import girderVuetifyConfig from '@girder/components/src/utils/vuetifyConfig';
import { merge } from 'lodash';

Vue.use(Vuetify);

const appVuetifyConfig = merge(girderVuetifyConfig, {
    icons: {

    },
});

export default new Vuetify(appVuetifyConfig);

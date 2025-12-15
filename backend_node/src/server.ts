import {createApp} from './app';
import {logger} from './config/logger';
import {env} from './config/env';

const app = createApp();

// app.listen(env.port, () => {
//     logger.info(`Server running in ${env.nodeEnv} mode on port ${env.port}`);
// });

module.exports = app;
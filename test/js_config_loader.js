import ConfigBroker from "../src/js/sigopt_config/broker";

const [configDir, method, key] = process.argv.slice(2);

ConfigBroker.fromDirectory(configDir).then((configBroker) => {
  const getConfig = ({
    get: configBroker.get,
    get_object: configBroker.getObject,
  })[method].bind(configBroker);
  configBroker.initialize(
    () => {
      console.log(JSON.stringify(getConfig(key)));
    },
  );
});

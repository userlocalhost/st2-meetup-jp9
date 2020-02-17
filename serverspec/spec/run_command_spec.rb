require 'spec_helper'

describe command 'st2 login ${ST2_USER} -p ${ST2_PASSWORD}' do
  its(:exit_status) { should eq 0 }

  before(:all) do
    @st2_container = get_st2_container()
    [
      "st2 pack install slack".split(),
      "cp /opt/stackstorm/packs/slack/slack.yaml.example /opt/stackstorm/configs/slack.yaml".split(),
      ["sed", "-ie", "s@webhook_url: .*@webhook_url: #{ENV.fetch('SLACK_WEBHOOK_URL')}@", "/opt/stackstorm/configs/slack.yaml"],
      ["sed", "-ie", "s@username: .*@username: #{ENV.fetch('SLACK_USERNAME')}@", "/opt/stackstorm/configs/slack.yaml"],
      "st2ctl reload --register-configs".split(),
    ].each do |command|
      @st2_container.exec(command)
    end
  end

  # test the action that runs target workflow would work properly
  context command("st2 run meetup_jp9.run_cmd host='127.0.0.1' cmd='id' slack_channel='#{ ENV.fetch('SLACK_CHANNEL') }'") do
    its(:exit_status) { should eq 0 }
  end
end

require 'serverspec'
require 'docker'

set :backend, :docker

def get_st2_container()
  Docker::Container.all().each do |container|
    if container.is_a? Docker::Container and container.info['Image'].match('stackstorm')
      return container
    end
  end
end

@st2_container = get_st2_container()

raise "StackStorm container has not been invoked yet" if @st2_container.nil?

# set StackStorm container as a backend container that test would be executed
set :docker_container, @st2_container.id


# deploy this pack to docker container before running each tests
RSpec.configure do |config|
  config.before(:all) do
    # Preparing for each configurations to test this workflow
    @st2_container = get_st2_container()

    # deploy files which are necessary for running testing workflow
    [
      'fixtures/init_scripts',
      '..'
    ].each do |file|
      @st2_container.archive_in(File.absolute_path("#{file}"), "/tmp", overwrite: true)
    end
    
    # initialize local git repository that is cloned from testing workflow
    [
      'tar -xf /tmp/init_scripts -C /usr/local/sbin',
      '/usr/local/sbin/init_meetup_jp9',
    ].each do |command|
      @st2_container.exec(command.split())
    end
  end
end

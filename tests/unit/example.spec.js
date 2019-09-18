import { expect } from 'chai';
import { shallowMount } from '@vue/test-utils';
import Home from '@/views/Home.vue';

describe('Home.vue', () => {
  it('Renders the home page', () => {
\    const wrapper = shallowMount(Home, {
      propsData: {},
    });
    expect(wrapper.text()).to.include("Welcome to 2ber");
  });
});

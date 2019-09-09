// https://docs.cypress.io/api/introduction/api.html

describe('Homepage smoke test', () => {
  it('Visits the app root url', () => {
    cy.visit('/');
    cy.contains('span', '2ber');
  });
});

// Matches file-api's JWT payload (app/security.py: create_access_token) -
// only the user id ("sub") is signed into the token. There is no project id
// in the token; file-api has one project per user, fetched via GET /users/me.
export type UserPrincipal = {
  sub: string;
};
